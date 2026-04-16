import typer

from app.seeds.service import run_all, run_categories, run_tags, run_users

app = typer.Typer(help="Seeds: users, categories, tags")


@app.command("all")
def all():
    run_all()
    typer.echo("All seeds executed successfully!")


@app.command("users")
def user():
    run_users()
    typer.echo("Users seeded successfully!")


@app.command("categories")
def categories():
    run_categories()
    typer.echo("Categories seeded successfully!")


@app.command("tags")
def tags():
    run_tags()
    typer.echo("Tags seeded successfully!")
