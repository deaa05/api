from fastapi import FastAPI
from models.item import Item
from models.form_data import FormData
from fastapi import FastAPI, Form, Response
from fastapi import FastAPI, Form
from typing import Annotated
from models.task import Task
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import requests
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client


load_dotenv()

def _build_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_PUBLISHABLE_KEY")
    if not url or not key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Faltan variables de entorno de Supabase (SUPABASE_URL / SUPABASE_PUBLISHABLE_KEY)."
        )
    return create_client(url, key)

security = HTTPBearer()

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "¡Hola, Fast API!"}

@app.get("/items/{item_id}")
def read_item(item_id: int):
   return {"item_id": item_id}

@app.get("/items/")
def read_item(skip: int = 0, limit: int = 10, q: str | None = None):
   results = fake_items_db[skip : skip + limit]
   if q:
      results.append({"item_name": q})
   return results


fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}, {"item_name": "Qux"}, {"item_name": "Quux"}, {"item_name": "Corge"}, {"item_name": "Grault"}, {"item_name": "Garply"}, {"item_name": "Waldo"}, {"item_name": "Fred"}, {"item_name": "Plugh"}, {"item_name": "Xyzzy"}, {"item_name": "Thud"}]
@app.post("/items/")
def create_item(item: Item):
   item_dict = item.model_dump()
   if item_dict is not None:
      fake_items_db.append(item_dict)
   return item_dict

@app.put("/items/{item_name}")
def update_item(item_name: str, item: Item):
   for i, fake_item in enumerate(fake_items_db):
      if fake_item["item_name"] == item_name:
         fake_items_db[i] = item.model_dump()
         return {"item_name": item_name, **item.model_dump()}
   return {"error": "Item not found"}

@app.put("/items/{item_name}/query")
def update_item_with_query(item_name: str, item: Item, q: str | None = None):
   for i, fake_item in enumerate(fake_items_db):
      if fake_item["item_name"] == item_name:
         fake_items_db[i] = item.model_dump()
         response = {"item_name": item_name, **item.model_dump()}
         if q:
            response.update({"q": q})
         return response
   return {"error": "Item not found"}



@app.post("/items_form/")
def create_item(
  item_name: Annotated[str, Form()],
  description: Annotated[str, Form()],
  price: Annotated[float, Form()],
  tax: Annotated[float, Form()]
):
    form_data = FormData(
      item_name=item_name,
      description=description,
      price=price,
      tax=tax
  )
    message = f"Item '{form_data.item_name}' created successfully with description '{form_data.description}', price {form_data.price}, and tax {form_data.tax}."
    fake_items_db.append(item_name)

    return Response(content=message, status_code=201)
    return message
    return {"item_name": item_name, "description": description, "price": price, "tax": tax}
    

@app.post("/tasks/")
def create_task(task: Task):
  supabase = _build_supabase_client()
  data = supabase.table("task").insert({
      "title": task.title,
      "description": task.description
  }).execute()
  return data.data

def get_supabase_client(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Client:
   token = credentials.credentials
   try:
      client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_PUBLISHABLE_KEY"))
      client.postgrest.auth(token)
      return client
   except Exception:
      raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de Supabase inválido o expirado"
      )
@app.get("/tasks/", status_code=status.HTTP_200_OK)
def get_tasks(supabase: Client = Depends(get_supabase_client)):
   try:
      response = supabase.table("task").select("*").execute()

      return response.data

   except Exception as e:
      raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al recuperar las tareas desde la base de datos."
      )
  
@app.post("/auth/login-temporal")
def login_temporal(email: str, password: str):
   # Endpoint nativo de Supabase Auth
   url = f"{os.getenv('SUPABASE_URL')}/auth/v1/token?grant_type=password"
   headers = {"apikey": os.getenv("SUPABASE_PUBLISHABLE_KEY"), "Content-Type": "application/json"}
   payload = {"email": email, "password": password}

   response = requests.post(url, json=payload, headers=headers)
   if response.status_code != 200:
      raise HTTPException(status_code=400, detail="Credenciales incorrectas en Supabase")

   # Retornamos el access_token que es el JWT que necesitas
   return {"access_token": response.json().get("access_token")}

