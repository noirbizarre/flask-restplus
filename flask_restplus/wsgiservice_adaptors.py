from wsgiservice.resource import Resource as wsgiservice_resource



def get_resource_http_methods(resource):
    '''
    Returns HTTP request handler methods defined on wsgiservice resource class

    Skips OPTIONS method.

    :param resource wsgiservice.Resource : wsgiservice Resource to be inspected
    '''
    if issubclass(resource,wsgiservice_resource):
        return [method for method in resource.KNOWN_METHODS if hasattr(resource, method) \
            and method != 'OPTIONS']
    else:
        return []
