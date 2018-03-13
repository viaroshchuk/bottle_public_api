import graphene
from graphene.types import datetime
import mysql_query
import pprint


class Note(graphene.ObjectType):
    date = graphene.types.datetime.DateTime()
    content = graphene.String()


class User(graphene.ObjectType):
    id = graphene.Int()
    name = graphene.String()
    notes = graphene.List(Note)

    def resolve_name(self, info):
        return mysql_query.exec_sql("SELECT profile_name FROM profiles WHERE id={}"
                                    .format(self.id))[1][0]['profile_name']

    def resolve_notes(self, info):
        db_notes = mysql_query.exec_sql("SELECT content, date FROM notes WHERE user_id={}".format(self.id))[1]
        return [Note(date=x['date'], content=x['content']) for x in db_notes]


class Query(graphene.ObjectType):
    user = graphene.Field(User, id=graphene.Int())

    def resolve_user(self, info, id):
        # Check if user exists
        if mysql_query.exec_sql("SELECT * FROM profiles WHERE id={}".format(id))[0]:
            return User(id=id)
        else:
            print('There are no user in db with id' + str(id))
            return None


def main():
    schema = graphene.Schema(query=Query)

    query = '''
        query getUser($id: Int){
          user(id: $id){
            name
            notes{
                date
                content
            }
          }
        }
    '''
    uid = input("Enter user id to fetch notes: ")
    result = schema.execute(query, variable_values={"id": int(uid)})

    pprint.pprint(result.data)


if __name__ == '__main__':
    main()

