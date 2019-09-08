import logging

import flask_restplus as restplus


class LoggingTest(object):
    def test_namespace_loggers_log_to_flask_app_logger(self, app, client, caplog):
        # capture Flask app logs
        caplog.set_level(logging.INFO, logger=app.logger.name)

        api = restplus.Api(app)
        ns1 = api.namespace('ns1', path='/ns1')
        ns2 = api.namespace('ns2', path='/ns2')

        @ns1.route('/')
        class Ns1(restplus.Resource):
            def get(self):
                ns1.logger.info("hello from ns1")
                pass

        @ns2.route('/')
        class Ns2(restplus.Resource):
            def get(self):
                ns2.logger.info("hello from ns2")
                pass

        # debug log not shown
        client.get("/ns1/")
        matching = [r for r in caplog.records if r.message == "hello from ns1"]
        assert len(matching) == 1

        # info log shown
        client.get("/ns2/")
        matching = [r for r in caplog.records if r.message == "hello from ns2"]
        assert len(matching) == 1

    def test_defaults_to_app_level(self, app, client, caplog):
        caplog.set_level(logging.INFO, logger=app.logger.name)

        api = restplus.Api(app)
        ns1 = api.namespace('ns1', path='/ns1')
        ns2 = api.namespace('ns2', path='/ns2')

        @ns1.route('/')
        class Ns1(restplus.Resource):
            def get(self):
                ns1.logger.debug("hello from ns1")
                pass

        @ns2.route('/')
        class Ns2(restplus.Resource):
            def get(self):
                ns2.logger.info("hello from ns2")
                pass

        # debug log not shown
        client.get("/ns1/")
        matching = [r for r in caplog.records if r.message == "hello from ns1"]
        assert len(matching) == 0

        # info log shown
        client.get("/ns2/")
        matching = [r for r in caplog.records if r.message == "hello from ns2"]
        assert len(matching) == 1

    def test_override_app_level(self, app, client, caplog):
        caplog.set_level(logging.INFO, logger=app.logger.name)

        api = restplus.Api(app)
        ns1 = api.namespace('ns1', path='/ns1')
        ns1.logger.setLevel(logging.DEBUG)
        ns2 = api.namespace('ns2', path='/ns2')

        @ns1.route('/')
        class Ns1(restplus.Resource):
            def get(self):
                ns1.logger.debug("hello from ns1")
                pass

        @ns2.route('/')
        class Ns2(restplus.Resource):
            def get(self):
                ns2.logger.debug("hello from ns2")
                pass

        # debug log shown from ns1
        client.get("/ns1/")
        matching = [r for r in caplog.records if r.message == "hello from ns1"]
        assert len(matching) == 1

        # debug not shown from ns2
        client.get("/ns2/")
        matching = [r for r in caplog.records if r.message == "hello from ns2"]
        assert len(matching) == 0

    def test_namespace_additional_handler(self, app, client, caplog, tmp_path):
        caplog.set_level(logging.INFO, logger=app.logger.name)
        log_file = tmp_path / "v1.log"

        api = restplus.Api(app)
        ns1 = api.namespace('ns1', path='/ns1')
        # set up a file handler for ns1 only
        # FileHandler only supports Path object on Python >= 3.6 -> cast to str
        fh = logging.FileHandler(str(log_file))
        ns1.logger.addHandler(fh)

        ns2 = api.namespace('ns2', path='/ns2')

        @ns1.route('/')
        class Ns1(restplus.Resource):
            def get(self):
                ns1.logger.info("hello from ns1")
                pass

        @ns2.route('/')
        class Ns2(restplus.Resource):
            def get(self):
                ns2.logger.info("hello from ns2")
                pass

        # ns1 logs go to stdout and log_file
        client.get("/ns1/")
        matching = [r for r in caplog.records if r.message == "hello from ns1"]
        assert len(matching) == 1
        with log_file.open() as f:
            assert "hello from ns1" in f.read()

        # ns2 logs go to stdout only
        client.get("/ns2/")
        matching = [r for r in caplog.records if r.message == "hello from ns2"]
        assert len(matching) == 1
        with log_file.open() as f:
            assert "hello from ns1" in f.read()
