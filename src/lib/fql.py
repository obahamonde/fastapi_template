from src.conf import env
from faunadb import query as q
from faunadb.client import FaunaClient
from faunadb.errors import FaunaError
from typing import Callable, List
from pydantic import BaseModel

from src.utils import tstamp

class FaunaMeta(BaseModel):
    id: str
    ts: float

fql: Callable = FaunaClient(env.FAUNA_SECRET).query

def meta(response: dict) -> FaunaMeta:
    return FaunaMeta(id=response['ref'].id(), ts=tstamp(response['ts']))

def createCollection(model: BaseModel):
    try:
        fql(
        q.if_(
            q.exists(q.collection(f"{model.__class__.__name__.lower()}s")),
            True,
            q.create_collection(
                {"name": f"{model.__class__.__name__.lower()}s"})))
        fql(q.create_index(
            {"name": f"{model.__class__.__name__}s", "source": q.collection(f"{model.__class__.__name__.lower()}s")}))
        fql(
            q.if_(
                q.exists(q.collection(f"{model.__class__.__name__.lower()}s")),
                True,
                q.create_collection(
                    {"name": f"{model.__class__.__name__.lower()}s"})))
        fql(q.create_index(
            {"name": f"{model.__class__.__name__}s", "source": q.collection(f"{model.__class__.__name__.lower()}s")}))
    except FaunaError as e:
        print(e)
        return False
    return True
    


def createFieldIndex(model: BaseModel, field: str):
    index = {
        "name": f"{model.__class__.__name__}_by_{field}".lower(),
        "source": q.collection(f"{model.__class__.__name__}s".lower()),
        "terms": [{
            "field": ["data", field]
        }]
    }
    response = fql(
        q.if_(q.exists(q.index(q.select("name", index))), True,
              q.create_index(index)))
    return response

def createSortIndex(model: BaseModel, field: str):
    index = {
        "name": f"{model.__class__.__name__}_sort_by_{field}".lower(),
        "source": q.collection(f"{model.__class__.__name__}s".lower()),
        "terms": [{
            "field": ["data", field]
        }],
        "values": [
            {
                "field": ["ref"]
            },
        ]
    }
    response = fql(
        q.if_(q.exists(q.index(q.select("name", index))), True,
              q.create_index(index)))
    return response

class Q:

    def create(model: BaseModel) -> FaunaMeta:
        createCollection(model)
        for field in model.__fields__:
            createFieldIndex(model, field)
            createSortIndex(model, field)
        try:
            response = fql(
                q.get(
                    q.match(
                        q.index(
                            f"{model.__class__.__name__}_by_{field}".lower()),
                        model.dict()[field])))
            return FaunaMeta(id=response['ref'].id(),
                             ts=float(
                                 str(response['ts'])[:10] + '.' +
                                 str(response['ts'])[10:]))
        except FaunaError as e:
            print(e)
            response = fql(
                q.create(q.collection(f"{model.__class__.__name__.lower()}s"),
                         {"data": model.dict()}))
            return meta(response)

    def read(cls: str, field: str, value: str) -> BaseModel:
        createCollection(cls)
        createFieldIndex(cls, field)
        createSortIndex(cls, field)
        try:
            response = fql(
                q.get(q.match(q.index(f"{cls}_by_{field}".lower()), value)))
            return response['data']
        except FaunaError as e:
            print(e)
            return None

    def update(cls: str, field: str, value: str, data: dict) -> FaunaMeta:
        try:
            response = fql(
                q.get(q.match(q.index(f"{cls}_by_{field}".lower()), value)))
            return meta(fql(q.update(response['ref'], {"data": data})))
        except FaunaError as e:
            print(e)
            return None

    def delete(cls: str, field: str, value: str) -> FaunaMeta:
        try:
            response = fql(
                q.get(q.match(q.index(f"{cls}_by_{field}".lower()), value)))
            return meta(fql(q.delete(response['ref'])))
        except FaunaError as e:
            print(e)
            return None

    def read_all(cls: str, limit: int) -> List[BaseModel]:
        try:
            index = {
                "name": f"{cls}s",
                "source": q.collection(f"{cls}s".lower())
            }
            fql(
                q.if_(q.exists(q.index(q.select("name", index))), True,
                      q.create_index(index)))
            refs = fql(q.paginate(q.match(f"{cls}s"), limit))['data']
            return [fql(q.get(ref))['data'] for ref in refs]
        except FaunaError as e:
            print(e)
            return []

    def read_many(cls: str, field: str, value: str) -> List[BaseModel]:
        try:
            index = {
                "name": f"{cls}_by_{field}".lower(),
                "source": q.collection(f"{cls}s".lower())
            }
            fql(
                q.if_(q.exists(q.index(q.select("name", index))), True,
                      q.create_index(index)))
            refs = fql(q.match(f"{cls}_by_{field}".lower(), value))
            return [fql(q.get(ref)) for ref in refs]
        except FaunaError as e:
            print(e)
            return []