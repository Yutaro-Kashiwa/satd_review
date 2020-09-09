import redis
class GerritDao:
    def __init__(self, project):
        self.projects_no = {'openstack': 1, 'qt': 2}
        self.project=project
        db_no = self._get_project_no()
        self.radis = redis.Redis(host='localhost', port=6379, db=db_no)
        pass

    def put(self, review_id, data):
        self.radis.set(review_id, data)
        pass

    def get(self, review_id):
        data = self.radis.get(review_id)
        #Jsonに戻す
        return data.decode()

    def list(self):
        return self.radis.scan_iter()


    def _get_project_no(self):
        return self.projects_no[self.project]

