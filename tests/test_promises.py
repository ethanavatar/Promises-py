from promises import Promise

def pass_cb(v):
    assert v

def fail_cb(v):
    assert not v

class TestThen:

    @staticmethod
    def test_then_no_chaining():
        Promise().then(pass_cb)

    @staticmethod
    def test_then_chaining():
        return Promise().then(pass_cb).then(pass_cb)

    @staticmethod
    def test_multiple_then():
        promise = Promise()
        first = promise.then(pass_cb)
        second = promise.then(pass_cb)
        return Promise.allSettled([first, second])

class TestCatch:

    @staticmethod
    def test_catch_no_chaining():
        return Promise().catch(fail_cb)

    @staticmethod
    def test_catch_chaining():
        return Promise().catch(fail_cb).catch(fail_cb)

    @staticmethod
    def test_multiple_catch():
        promise = Promise()
        first = promise.catch(fail_cb)
        second = promise.catch(fail_cb)
        return Promise.allSettled([first, second])