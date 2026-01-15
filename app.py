import os
from flask import (
    Flask,
    request,
    jsonify,
    abort,
    render_template,
    flash,
    session,
    redirect,
    url_for,
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from functools import wraps
import json

load_dotenv()

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    "?charset=utf8mb4"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)


def ensure_admin_user():
    # creează admin/admin123 dacă nu există
    u = User.query.filter_by(username="admin").first()
    if not u:
        u = User(username="admin", password_hash=generate_password_hash("admin123"))
        db.session.add(u)
        db.session.commit()


with app.app_context():
    db.create_all()
    ensure_admin_user()


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin_user"):
            return redirect(url_for("admin_login", next=request.path))
        return fn(*args, **kwargs)

    return wrapper


def clamp(x, lo, hi, d):
    try:
        x = int(x)
    except:
        return d
    return max(lo, min(hi, x))


# LIST: paginare + search + filtre
@app.get("/api/wows")
def list_wows():
    page = clamp(request.args.get("page"), 1, 10000, 1)
    per_page = clamp(request.args.get("per_page"), 1, 100, 20)

    q = (request.args.get("q") or "").strip()
    movie = (request.args.get("movie") or "").strip()
    year = (request.args.get("year") or "").strip()

    where = []
    params = {}

    if movie:
        where.append("movie = :movie")
        params["movie"] = movie

    if year:
        where.append("year = :year")
        params["year"] = int(year)

    if q:
        where.append(
            """
        (
          movie LIKE :q OR
          director LIKE :q OR
          role_name LIKE :q OR
          full_line LIKE :q
        )
        """
        )
        params["q"] = f"%{q}%"

    where_sql = "WHERE " + " AND ".join(where) if where else ""

    total = (
        db.session.execute(
            db.text(f"SELECT COUNT(*) total FROM v_wows {where_sql}"), params
        )
        .mappings()
        .first()["total"]
    )

    offset = (page - 1) * per_page

    rows = (
        db.session.execute(
            db.text(
                f"""
        SELECT id, movie, year, director, role_name, full_line, image_data_uri
        FROM v_wows
        {where_sql}
        ORDER BY id
        LIMIT :limit OFFSET :offset
    """
            ),
            {**params, "limit": per_page, "offset": offset},
        )
        .mappings()
        .all()
    )

    return jsonify(
        {
            "page": page,
            "per_page": per_page,
            "total": int(total),
            "items": [dict(r) for r in rows],
        }
    )


# DETAIL PAGE
@app.get("/api/wows/<int:wow_id>")
def wow_detail(wow_id):
    row = (
        db.session.execute(
            db.text(
                """
            SELECT *
            FROM v_wows
            WHERE id = :id
        """
            ),
            {"id": wow_id},
        )
        .mappings()
        .first()
    )

    if not row:
        abort(404)

    return jsonify(dict(row))


@app.get("/")
def web_list():
    page = clamp(request.args.get("page"), 1, 10000, 1)
    per_page = clamp(request.args.get("per_page"), 1, 100, 12)

    q = (request.args.get("q") or "").strip()
    movie = (request.args.get("movie") or "").strip()
    year = (request.args.get("year") or "").strip()

    where = []
    params = {}

    if movie:
        where.append("LOWER(movie) = LOWER(:movie)")
        params["movie"] = movie

    if year:
        where.append("year = :year")
        params["year"] = int(year)

    if q:
        where.append(
            """
            (
              LOWER(movie)     LIKE LOWER(:q) OR
              LOWER(director)  LIKE LOWER(:q) OR
              LOWER(role_name) LIKE LOWER(:q) OR
              LOWER(full_line) LIKE LOWER(:q)
            )
            """
        )
        params["q"] = f"%{q}%"

    where_sql = "WHERE " + " AND ".join(where) if where else ""

    total = (
        db.session.execute(
            db.text(f"SELECT COUNT(*) total FROM v_wows {where_sql}"), params
        )
        .mappings()
        .first()["total"]
    )

    offset = (page - 1) * per_page

    rows = (
        db.session.execute(
            db.text(
                f"""
                SELECT id, movie, year, director, role_name, full_line, image_data_uri
                FROM v_wows
                {where_sql}
                ORDER BY id
                LIMIT :limit OFFSET :offset
                """
            ),
            {**params, "limit": per_page, "offset": offset},
        )
        .mappings()
        .all()
    )

    pages = max(1, (int(total) + per_page - 1) // per_page)

    movies = [
        r["movie"]
        for r in db.session.execute(
            db.text(
                "SELECT DISTINCT movie FROM v_wows WHERE movie IS NOT NULL ORDER BY movie"
            )
        )
        .mappings()
        .all()
    ]

    years = [
        int(r["year"])
        for r in db.session.execute(
            db.text(
                "SELECT DISTINCT year FROM v_wows WHERE year IS NOT NULL ORDER BY year DESC"
            )
        )
        .mappings()
        .all()
    ]

    return render_template(
        "list.html",
        items=[dict(r) for r in rows],
        page=page,
        per_page=per_page,
        total=int(total),
        pages=pages,
        q=q,
        movie=movie,
        year=year,
        movies=movies,
        years=years,
    )


@app.get("/wows/<int:wow_id>")
def web_detail(wow_id: int):
    row = (
        db.session.execute(
            db.text("SELECT * FROM v_wows WHERE id = :id"),
            {"id": wow_id},
        )
        .mappings()
        .first()
    )

    if not row:
        abort(404)

    # 🔽 AICI ADAUGI
    item = dict(row)

    # video_json -> dict sigur pentru template
    video = None
    try:
        if isinstance(item.get("video_json"), str):
            video = json.loads(item["video_json"])
        elif isinstance(item.get("video_json"), dict):
            video = item["video_json"]
    except Exception:
        video = None

    item["video"] = video

    try:
        item["raw_pretty"] = json.dumps(
            item.get("raw_json"), indent=2, ensure_ascii=False
        )
    except Exception:
        item["raw_pretty"] = str(item.get("raw_json"))

    # 🔽 ȘI AICI SE TERMINĂ
    return render_template("detail.html", item=item)


@app.get("/admin/login")
def admin_login():
    return render_template(
        "admin_login.html", next=request.args.get("next") or "/admin"
    )


@app.post("/admin/login")
def admin_login_post():
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    next_url = request.form.get("next") or "/admin"

    u = User.query.filter_by(username=username).first()
    if not u or not check_password_hash(u.password_hash, password):
        flash("Credențiale greșite.", "danger")
        return redirect(url_for("admin_login", next=next_url))

    session["admin_user"] = u.username
    return redirect(next_url)


@app.post("/admin/logout")
@admin_required
def admin_logout():
    session.pop("admin_user", None)
    return redirect(url_for("admin_login"))


@app.get("/admin")
@admin_required
def admin_panel():
    # listare simplă cu paginare + search
    page = clamp(request.args.get("page"), 1, 10000, 1)
    per_page = clamp(request.args.get("per_page"), 1, 100, 20)
    q = (request.args.get("q") or "").strip()

    where = []
    params = {}

    if q:
        where.append(
            """
            (
              LOWER(movie)     LIKE LOWER(:q) OR
              LOWER(director)  LIKE LOWER(:q) OR
              LOWER(role_name) LIKE LOWER(:q) OR
              LOWER(full_line) LIKE LOWER(:q)
            )
            """
        )
        params["q"] = f"%{q}%"

    where_sql = "WHERE " + " AND ".join(where) if where else ""
    total = (
        db.session.execute(
            db.text(f"SELECT COUNT(*) total FROM v_wows {where_sql}"), params
        )
        .mappings()
        .first()["total"]
    )

    offset = (page - 1) * per_page
    rows = (
        db.session.execute(
            db.text(
                f"""
                SELECT id, movie, year, director, role_name, full_line
                FROM v_wows
                {where_sql}
                ORDER BY id
                LIMIT :limit OFFSET :offset
                """
            ),
            {**params, "limit": per_page, "offset": offset},
        )
        .mappings()
        .all()
    )

    pages = max(1, (int(total) + per_page - 1) // per_page)

    return render_template(
        "admin_list.html",
        items=[dict(r) for r in rows],
        page=page,
        per_page=per_page,
        pages=pages,
        total=int(total),
        q=q,
        admin_user=session.get("admin_user"),
    )


def json_pretty(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False)


def validate_data_uri(image_str: str) -> bool:
    if not image_str:
        return True
    return image_str.startswith("data:image/") and ";base64," in image_str


def as_int(v, default=0):
    try:
        return int(v)
    except Exception:
        return default


def obj_to_form(obj: dict) -> dict:
    video = obj.get("video") or {}
    return {
        "movie": obj.get("movie", ""),
        "year": obj.get("year", ""),
        "release_date": obj.get("release_date", ""),
        "director": obj.get("director", ""),
        "character": obj.get("character", ""),
        "movie_duration": obj.get("movie_duration", ""),
        "timestamp": obj.get("timestamp", ""),
        "full_line": obj.get("full_line", ""),
        "current_wow_in_movie": obj.get("current_wow_in_movie", 1),
        "total_wows_in_movie": obj.get("total_wows_in_movie", 1),
        "audio": obj.get("audio", ""),
        "image": obj.get("image", ""),
        "video_1080p": video.get("1080p", ""),
        "video_720p": video.get("720p", ""),
        "video_480p": video.get("480p", ""),
        "video_360p": video.get("360p", ""),
    }


def form_to_obj(form) -> dict:
    return {
        "movie": (form.get("movie") or "").strip(),
        "year": as_int(form.get("year"), 2000),
        "release_date": (form.get("release_date") or "").strip(),
        "director": (form.get("director") or "").strip(),
        "character": (form.get("character") or "").strip(),
        "movie_duration": (form.get("movie_duration") or "").strip(),
        "timestamp": (form.get("timestamp") or "").strip(),
        "full_line": (form.get("full_line") or "").strip(),
        "current_wow_in_movie": as_int(form.get("current_wow_in_movie"), 1),
        "total_wows_in_movie": as_int(form.get("total_wows_in_movie"), 1),
        "audio": (form.get("audio") or "").strip(),
        "image": (form.get("image") or "").strip(),
        "video": {
            "1080p": (form.get("video_1080p") or "").strip(),
            "720p": (form.get("video_720p") or "").strip(),
            "480p": (form.get("video_480p") or "").strip(),
            "360p": (form.get("video_360p") or "").strip(),
        },
    }


@app.get("/admin/new")
@admin_required
def admin_new():
    template = {
        "movie": "",
        "year": 2000,
        "release_date": "",
        "director": "",
        "character": "",
        "movie_duration": "",
        "timestamp": "",
        "full_line": "",
        "current_wow_in_movie": 1,
        "total_wows_in_movie": 1,
        "video": {"1080p": "", "720p": "", "480p": "", "360p": ""},
        "audio": "",
        "image": "data:image/png;base64,",
    }
    return render_template(
        "admin_form.html", mode="new", id=None, f=obj_to_form(template)
    )


@app.post("/admin/new")
@admin_required
def admin_new_post():
    obj = form_to_obj(request.form)

    if obj.get("image") and not validate_data_uri(obj["image"]):
        flash(
            "Câmpul image trebuie să fie Data URI (data:image/...;base64,...).",
            "danger",
        )
        return render_template(
            "admin_form.html", mode="new", id=None, f=obj_to_form(obj)
        )

    db.session.execute(
        db.text("INSERT INTO data (data) VALUES (:data)"),
        {"data": json.dumps(obj, ensure_ascii=False)},
    )
    db.session.commit()
    flash("Înregistrare adăugată.", "success")
    return redirect(url_for("admin_panel"))


@app.get("/admin/edit/<int:item_id>")
@admin_required
def admin_edit(item_id: int):
    row = (
        db.session.execute(
            db.text("SELECT id, data FROM data WHERE id = :id"), {"id": item_id}
        )
        .mappings()
        .first()
    )
    if not row:
        abort(404)

    obj = row["data"]
    if isinstance(obj, str):
        obj = json.loads(obj)

    return render_template(
        "admin_form.html", mode="edit", id=item_id, f=obj_to_form(obj)
    )


@app.post("/admin/edit/<int:item_id>")
@admin_required
def admin_edit_post(item_id: int):
    obj = form_to_obj(request.form)

    if obj.get("image") and not validate_data_uri(obj["image"]):
        flash(
            "Câmpul image trebuie să fie Data URI (data:image/...;base64,...).",
            "danger",
        )
        return render_template(
            "admin_form.html", mode="edit", id=item_id, f=obj_to_form(obj)
        )

    res = db.session.execute(
        db.text("UPDATE data SET data = :data WHERE id = :id"),
        {"data": json.dumps(obj, ensure_ascii=False), "id": item_id},
    )
    db.session.commit()

    if res.rowcount == 0:
        abort(404)

    flash("Înregistrare salvată.", "success")
    return redirect(url_for("admin_panel"))


@app.post("/admin/delete/<int:item_id>")
@admin_required
def admin_delete(item_id: int):
    db.session.execute(db.text("DELETE FROM data WHERE id = :id"), {"id": item_id})
    db.session.commit()
    flash("Înregistrare ștearsă.", "success")
    return redirect(url_for("admin_panel"))


app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
if __name__ == "__main__":
    app.run(debug=True)
