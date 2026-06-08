"""Uvicorn entry point for Skills Agent + Distiller web server."""

import uvicorn


def main():
    uvicorn.run(
        "langchain_skills.api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
