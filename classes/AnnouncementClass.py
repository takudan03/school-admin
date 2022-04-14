import pymongo

class Announcement:
    id = ''
    client = pymongo.MongoClient(port=27017)
    db = client.school_admin

    def __init__(self, title, body, recepients):
        # TODO generate some id
        #self.id=announcnement_count_index
        self.title=title
        self.body=body
        self.recepients=recepients
        self.set_id()


    def set_id(self, id=None):
        if id == None:
            # query=db.announcements.find_one({'title':title})
            # if query.retrieved==0:
            ann_index = self.db.db_indices.find_one({'_id': 'index_ann'})['curr_index']
            res = self.db.db_indices.update_one({'_id': 'index_ann'},
                                           {'$inc': {'curr_index': 1}},
                                           upsert=True
                                           )
            self.id = 'ANN' + str(ann_index).rjust(5, '0')
        else:
            self.id = id
