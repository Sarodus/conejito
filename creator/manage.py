from app import CreatorApp

if __name__ == "__main__":
    app = CreatorApp(
        template_folder='/data/creator/app/templates/'
    )
    app.run(host='0.0.0.0')
