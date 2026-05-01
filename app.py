from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
    # http://localhost:5000/

    @app.errorhandler(403)
    def forbidden(e):
        return f"403 triggered by: {e}", 403