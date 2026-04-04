# def add(a, b):
#     return a + b
#
# if __name__ == '__main__':
#     print(f'Sum: {add(1, 2)}')
from fastapi import FastAPI



def fastapi_01()->FastAPI:
    app:FastAPI = FastAPI(
        title="PythonP Color API",
        description="CIE 1931",
        version="0.1.0"
    )
    
    @app.get("/")
    async def root()->dict[str, str]:
        return {"message": "Hello World"}

    return app

app:FastAPI = fastapi_01()
