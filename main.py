from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi.responses import JSONResponse

from crud import crud_service, user_crud_service
import schema
from auth import pwd_context, authenticate_user, create_access_token, get_current_user

app = FastAPI()

class Settings(BaseModel):
    authjwt_secret_key: str = "your_secret_key"

settings = Settings()

@AuthJWT.load_config
def get_config():
    return settings

@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )

@app.post("/signup")
def signup(user: schema.UserCreate):
    db_user = user_crud_service.get_user_by_username(username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = pwd_context.hash(user.password)
    return user_crud_service.create_user(user_data=user, hashed_password=hashed_password)

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.get('username')})
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.get('id')}

@app.post("/books")
def create_book(book_data: schema.BookCreate, user: schema.UserBase = Depends(get_current_user)):
    book = crud_service.create_book(book_data)
    return {"message": "Book created successfully!", "data": book}

@app.get("/books", dependencies=[Depends(get_current_user)])
def get_all_books(skip: int = 0, limit: int = 10, user: schema.UserBase = Depends(get_current_user)):
    books = crud_service.get_all_books(skip, limit)
    return {"data": books}

@app.get("/books/{book_id}", dependencies=[Depends(get_current_user)])
def get_book_by_id(book_id: str, user: schema.UserBase = Depends(get_current_user)):
    book = crud_service.get_book_by_id(book_id)
    if not book:
        return {"message": "Book not found"}
    return {"data": book}

@app.put("/books/{book_id}", dependencies=[Depends(get_current_user)])
def update_book(book_id: str, book_data: schema.BookUpdate, user: schema.UserBase = Depends(get_current_user)):
    book = crud_service.update_book(book_id, book_data)
    if not book:
        raise HTTPException(detail="Book not found", status_code=status.HTTP_400_BAD_REQUEST)
    return {"message": "Book updated successfully!", "data": book}

@app.delete("/books/{book_id}", dependencies=[Depends(get_current_user)])
def delete_book(book_id: str, user: schema.UserBase = Depends(get_current_user)):
    result = crud_service.delete_book(book_id)
    if not result:
        raise HTTPException(detail="Book not found", status_code=status.HTTP_400_BAD_REQUEST)
    return {"message": "Book deleted successfully!"}
