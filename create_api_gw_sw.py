#!/usr/bin/env python

from pprint import pprint
import requests
import json
import boto3
import botocore
import os
import argparse
import urllib
import sys
import logging
import re
import array
import time
# import pydevd

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

#HostedZoneId = 'Z8PFO4KLEZIYN'


def check_url(url, wait):
    while requests.get(url).status_code != 200:
        print "No/wrong response from api"
        if not wait:
            exit()
        time.sleep(10)
        next


def get_api_json(url):
    """
    :param url:
    :return: json string for API
    """
    url_api = url + "/api"
    try:
        response = urllib.urlopen(url_api)
        api_doc = json.loads(response.read())
    except Exception as e:
        logger.fatal("API read failed: %s" % e)
        exit()
    try:
        # Validate API
        if 'swagger' not in api_doc or api_doc['swagger'] != '2.0':
            raise ValueError("Not a swagger 2.0 doc.")
    except Exception as e:
        logger.fatal("API creation failed: %s" % e)
        exit()

    return api_doc


def generate_api_name(env_name, api_doc):
    api_title = api_doc['info']['title']
    api_doc['info']['title'] = '%s %s' % (env_name, api_title)
    logger.info('Set API name to: {}'.format(api_doc['info']['title']))
    return api_doc


def find_similar_api_name(api_name, region):
    list_api_names = []
    list_api_ids = []
    list_api_ids_to_del = []
    client = boto3.client('apigateway', region_name=region)
    response = client.get_rest_apis(
        limit=123
    )

    for api in response['items']:
        list_api_names.append(api['name'])
        list_api_ids.append(api['id'])
    for i in range(0, len(list_api_names)):
        if api_name == list_api_names[i]:
            list_api_ids_to_del.append(list_api_ids[i])
    return list_api_ids_to_del


def delete_api_gw(api_id_list, region):
    if len(api_id_list) == 0:
        logger.info('Nothing to delete')
        return
    client = boto3.client('apigateway', region_name=region)
    for i in api_id_list:
        try:
            response = client.delete_rest_api(
                restApiId=i
            )
        except Exception as e:
            logger.fatal("API deletion failed: %s" % e)
            logger.fatal("Waiting 60 sec. before next attempt...")
            time.sleep(60)
            response = client.delete_rest_api(
                restApiId=i
            )
            time.sleep(60)


''' Depricated Method, use substitude token instead
    Vendor fields generated in flask restplus.
'''
def configure_api(api_doc, url):
    '''Wire up API to API GW

    :add proxy integration to each AWS API GW endpoint
    '''
    list_paths = []
    dict_paths = {}

    for i in api_doc['paths']:
        list_paths.append(i)

    for i in list_paths:
        dict_paths[i] = api_doc['paths'][i].keys()[0]

    for i in list_paths:
        method = dict_paths[i]
        uri = url + i
        data_add = {"responses": {"default": {"statusCode": "200"}}, "uri": uri,
                    "passthroughBehavior": "when_no_match", "httpMethod": method, "type": "http_proxy"}
        api_doc['paths'][i][method]['x-amazon-apigateway-integration'] = data_add
    return api_doc

def substitute_token(data, token, replacement_string):
    data = json.loads(json.dumps(data).replace(token, replacement_string))
    return data

def configure_ep_url(api_doc, token, url):
    list_paths = []
    for path in api_doc['paths']:
        list_paths.append(path)
    for path in list_paths:
        api_doc['paths'][path] = substitute_token(api_doc['paths'][path], token, url+path)
    return api_doc



def create_api(api_json, region):
    """Create an API defined in Swagger.

    :param swagger_file_name: The name of the swagger file.
                              Full or relative path.
    :return: The id of the REST API.
    """

    client = boto3.client('apigateway', region_name=region)
    try:
        api_response = client.import_rest_api(
            failOnWarnings=True,
            body=api_json
        )
    except Exception as e:
        logger.fatal("API creation failed: %s" % e)
        exit()

    return api_response['id']


def deploy_api(api_id, stage, api_json, region):
    """Deploy API to the given stage.

    :param api_id: The id of the API.
    :param swagger_file: The name of the swagger file. Full or relative path.
    :param stage: The name of the stage to deploy to.
    :return: Tuple of Rest API ID, stage and Enpoint URL.
    """
    client = boto3.client('apigateway', region_name=region)

    api_def = json.loads(api_json)
    logger.info("deploying: " + api_id + " to " + stage)

    deploy_id = client.create_deployment(
                            restApiId=api_id,
                            stageName=stage,
                            cacheClusterEnabled=True,
                            cacheClusterSize='1.6',
                            )

    response_update = client.update_stage(
                            restApiId=api_id,
                            stageName=stage,
                            patchOperations=[
                                {
                                    'op': 'replace',
                                    'path': '/*/*/caching/ttlInSeconds',
                                    'value': '3600'
                                },
                                {
                                    'op': 'replace',
                                    'path': '/*/*/metrics/enabled',
                                    'value': 'true'
                                },
                                {
                                    'op': 'replace',
                                    'path': '/*/*/logging/loglevel',
                                    'value': 'info'
                                }
                                ]
                            )

    # print the end points
    logger.info("--------------------- END POINTS (START) ---------------")
    for path, path_object in api_def["paths"].iteritems():
        logger.info("End Point: https://%s"
                    ".execute-api.%s.amazonaws.com/"
                    "%s%s" % (api_id, region, stage, path))
    logger.info("--------------------- END POINTS (END) -----------------")

    enpoint_url = ("https://%s"
                   ".execute-api.%s.amazonaws.com/"
                   "%s" % (api_id, region, stage))
    return api_id, stage, enpoint_url

def dns_alias(stage_url, url, region):
    env_name = re.search('[dq]c-[0-9][0-9]', url).group()
    split_url = url.split('.peruze.us')[0]
    split_url = split_url.split('http://')[1]
    service_name = re.search('[a-z][a-z]*-[a-z].*', split_url).group()
    dns_alias_url = "{0}.{1}.peruze.us." .format(service_name, env_name)
    route53_alias_url = "{0}.{1}.peruze.us" .format(service_name, env_name)

    stage_url_ = str(stage_url)
    logger.info("Debug: {}" .format(stage_url))
    logger.info("Debug: {}".format(stage_url_))

    route53_client = boto3.client('route53', region_name=region)
    paginator = route53_client.get_paginator('list_resource_record_sets')
    response = paginator.paginate(
        HostedZoneId=HostedZoneId
    )
    res_list = []
    for pages in response:
        for res in pages['ResourceRecordSets']:
            res_list.append(res['Name'])
    if route53_alias_url in res_list:
        logger.info("{0} already exist. Skipping alias creation")
    else:
        response = route53_client.change_resource_record_sets(
            HostedZoneId=HostedZoneId,
            ChangeBatch={
                'Comment': '',
                'Changes': [
                    {
                        'Action': 'CREATE',
                        'ResourceRecordSet': {
                            'Name': dns_alias_url,
                            'Type': 'A',
                            'SetIdentifier': 'string',
                            'Region': region,
                            'AliasTarget': {
                                'HostedZoneId': HostedZoneId,
                                'DNSName': stage_url_,
                                'EvaluateTargetHealth': False
                            }
                        }
                    }

                ]
            }
        )
        pprint(response)

def fix_sg(sg_id, region):
    'Open up the app\'s inbound SG to all 10.x.x.x sources'
    ec2 = boto3.resource('ec2', region_name=region)
    sg = ec2.SecurityGroup(sg_id)
    try:
        sg.authorize_ingress(IpProtocol="tcp",CidrIp="0.0.0.0/0",FromPort=80,ToPort=80) 
    except botocore.exceptions.ClientError, e:
        if e.response['Error']['Code'] != 'InvalidPermission.Duplicate':
            raise e
    except Exception, e:
        raise e

def main(argv=None):
    if argv is None:
        argv = sys.argv

    #
    #  Parse command line arguments.
    #
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Deploy a URLs /api swagger doc to API GW')
    parser.add_argument(
        '-r', '--region', required=True,
        help='Region', metavar='REGION', default='us-west-2')
    parser.add_argument(
        '-u', '--url', required=True,
        help='API swagger doc URL', metavar='NAME')
    parser.add_argument(
        '-e', '--env', required=True,
        help='Env name suffix for API GW title.')
    parser.add_argument(
        '-s', '--elb_sg', required=True,
        help='App\'s exernal ELB\'s SG.')
    parser.add_argument(
        '-x', '--exturl', required=True,
        help='External URL for proxy endpoint', metavar='NAME')
    parser.add_argument(
        '-t', '--token', required=True,
        help='Token that will replaced by url', metavar='NAME')
    parser.add_argument(
        '-w', '--wait', action='store_true',
        help='Wait for URL to come up')
    parser.add_argument(
        '-D', '--delete', action='store_true',
        help='Delete APIs with the same name before creation')
    parser.add_argument(
        '-d', '--domain', required=False,
        help='DNS zone (NOT WORKING!!!)')
    parser.add_argument(
        '-v', '--verbose',
        default=False,
        action='store_true',
        help='enable verbose output')


    args = parser.parse_args(argv[1:])
    url = args.url
    exturl = args.exturl
    env = args.env
    region = args.region
    wait = args.wait
    delete = args.delete
    token = args.token

    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('boto3').setLevel(logging.WARNING)
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)-15s %(levelname)8s: %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(levelname)8s: %(message)s')

    logger.info('Creating API GW for %s, from url %s exported as %s', env, url, exturl)

    # pydevd.settrace('dc-02-ml-api', port=$SERVER_PORT, stdoutToServer = True, stderrToServer = True)
    # pydevd.settrace('dc-02-ml-api', stdoutToServer = True, stderrToServer = True)

    check_url(url, wait)

    api_dict = get_api_json(url)

    api_json = json.dumps(api_dict)

    # If env arg provided (required), customize API name with env suffix
    if env:
        api_dict = generate_api_name(env, api_dict)

    if delete:
        api_id_list = find_similar_api_name(api_dict['info']['title'], region)
        logger.info('API id to delete: %s' % (api_id_list))
        delete_api_gw(api_id_list, region)

    # DEPRICATED: configured_api = configure_api(api_dict, exturl)

    # Wire up API to AWS API GW
    configured_api = configure_ep_url(api_dict, token, exturl)

    # Generate API
    api_id = create_api(json.dumps(configured_api), region)
    print "api_id: ", api_id

    # deploy
    stage = 'dev'

    deploy_response = deploy_api(api_id, stage, api_json, region)
    stage_url = deploy_response[-1]

    fix_sg(args.elb_sg, region)

    # Not works yet
    # dns_alias(stage_url, url, region)


if __name__ == "__main__":
    sys.exit(main())
