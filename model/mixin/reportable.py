# if __name__ == '__main__':
#     import os, sys
#     sys.path.append('../../')
#     print(sys.path)

from mongoengine import *
from mongoengine.document import Document
from mongoengine.fields import *
from model.user import User
from model.mixin.chkable import Chkable
from mongoengine.queryset import *

class Report(Document, Chkable):
    resource = GenericReferenceField(primary_key=True)
    reporters = ListField(LazyReferenceField(User, reverse_delete_rule=PULL))


class Reportable():
    """可被举报的Mixin"""

    def report(self, user):
        r = Report.chk(self).modify(add_to_set__reporters=user)
        

# if __name__ == '__main__':
    
    
#     class Sample(Reportable, Document):
#         aa = StringField(primary_key=True)
#     class Sample2(Reportable, Document):
#         aa = StringField()
    
#     connect(host='mongodb://localhost:27017/testOJ')
#     u = User(pk='Testernfdjualdsjvnfdjsklnr').save()
#     u2 = User(pk='Testernfdacedsfgafdasfgds').save()
    
#     s1 = Sample(aa='234').save()
#     s2 = Sample2(aa='234').save()

#     s1.report(u)
#     s1.report(u)
#     s2.report(u)

#     s1.report(u2)
#     s2.report(u2)
#     s2.report(u2)

    # u.delete()


