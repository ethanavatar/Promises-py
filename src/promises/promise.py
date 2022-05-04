from enum import IntEnum

class STATE(IntEnum):
    PENDING = 0
    RESOLVED = 1
    REJECTED = 2

class UncaughtPromiseException(Exception):
    def __init__(self, e : Exception):
        self.message = f'(in promise) {e}'

class AggregatePromiseException(Exception):
    def __init__(self, exceptions : list):
        self.message = f'All promises rejected: {exceptions}'

class Promise:
    def __init__(self, callback):
        self.callback = callback
        self.thenCallbacks = []
        self.catchCallbacks = []
        self.value = None
        self.state = STATE.PENDING

        try:
            callback(self._onSuccess, self._onFail)
        except Exception as e:
            self._onFail(e)

    @classmethod
    def resolve(cls, value):
        return Promise(lambda resolve: resolve(value))

    @classmethod
    def reject(cls, e):
        return Promise(lambda resolve, reject: reject(e))

    @classmethod
    def all(cls, promises):
        results = []
        commpleted = 0
        return Promise(
            lambda resolve, reject:
                cls._gatherAll(promises, results, commpleted, resolve, reject)
        )

    @staticmethod
    def _gatherAll(promises, results, completed, resolve, reject):
        for promise in promises:
            promise.then(
                lambda value: Promise._completeAll(value, completed, results, len(promises), resolve, reject),
            ).catch(reject)

    @staticmethod
    def _completeAll(value, completed, results, total, resolve, reject):
        completed += 1
        results.append(value)

        if completed == total:
            resolve(results)

    @classmethod
    def allSettled(cls, promises):
        results = []
        commpleted = 0
        return Promise(
            lambda resolve:
                cls._gatherAllSettled(promises, results, commpleted, resolve)
        )

    @staticmethod
    def _gatherAllSettled(promises, results, completed, resolve):
        for promise in promises:
            promise.then(
                lambda value: results.append( (STATE.RESOLVED, value) )
            ).catch(
                lambda e: results.append( (STATE.REJECTED, e) )
            ).lastly(
                Promise._completeAllSettled(results, completed, len(promises), resolve)
            )

    @staticmethod
    def _completeAllSettled(value, completed, results, total, resolve):
        completed += 1
        if completed == total:
            resolve(results)

    @classmethod
    def race(cls, promises):
        return Promise(
            lambda resolve, reject: cls._race(promises, resolve, reject)
        )

    @staticmethod
    def _race(promises, resolve, reject):
        for promise in promises:
            promise.then(resolve).catch(reject)

    @classmethod
    def any(cls, promises):
        errors = []
        rejections = 0
        return Promise(
            lambda resolve, reject:
                cls._gatherAny(promises, errors, rejections, resolve, reject)
        )

    @staticmethod
    def _gatherAny(promises, results, completed, resolve, reject):
        for promise in promises:
            promise.then(resolve).catch(
                lambda e: Promise._completeAny(e, completed, results, len(promises), resolve, reject)
            )

    @staticmethod
    def _completeAny(value, rejections, errors, total, resolve, reject):
        rejections += 1
        errors.append(value)

        if rejections == total:
            reject( AggregatePromiseException(errors) )
    
    def runCallbacks(self):
        if self.state == STATE.RESOLVED:

            for callback in self.thenCallbacks:
                try:
                    callback(self.value)
                except Exception as e:
                    self._onFail(e)

            self.thenCallbacks = []

        if self.state == STATE.REJECTED:

            for callback in self.catchCallbacks:
                try:
                    callback(self.value)
                except Exception as e:
                    self._onFail(e)

            self.catchCallbacks = []

    def then(self, then=None, catch=None):
        return Promise(
            lambda resolve, reject:\
                self.thenCallbacks.append(lambda result: self._thenResult(result, then, resolve, reject)) and
                self.catchCallbacks.append(lambda result: self._catchResult(result, catch, resolve, reject))
        )

    def _thenResult(self, result, callback, resolve, reject):
        if not callback:
            resolve(result)
            return
        
        try:
            resolve(callback(result))
        except Exception as e:
            reject(e)

    def _catchResult(self, result, callback, resolve, reject):
        if not callback:
            reject(result)
            return
        
        try:
            resolve(callback(result))
        except Exception as e:
            reject(e)

    def catch(self, callback):
        self.then(None, callback)

    def lastly(self, callback):
        self.then(
            lambda value: self._lastlyResolve(value, callback),
            lambda e: self._lastlyReject(e, callback)
        )

    def _lastlyResolve(self, value, callback):
        callback()
        return value

    def _lastlyReject(self, e, callback):
        callback()
        raise e

    def _onSuccess(self, value):

        if self.state != STATE.PENDING:
            return

        if isinstance(value, Promise):
            value.then(self._onSuccess, self._onFail)
            return

        self.value = value
        self.state = STATE.RESOLVED

    def _onFail(self, e):
        if self.state != STATE.PENDING:
            return

        if isinstance(e, Promise):
            e.then(self._onSuccess, self._onFail)
            return

        if len(self.catchCallbacks) == 0:
            raise UncaughtPromiseException(e)

        self.value = e
        self.state = STATE.REJECTED

if __name__ == '__main__':
    Promise(
        lambda resolve, reject: resolve(1) and reject(2)
    )