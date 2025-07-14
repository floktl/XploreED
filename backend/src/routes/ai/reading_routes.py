from app.imports.imports import ai_bp

@ai_bp.route("/reading-exercise", methods=["POST"])
def reading_exercise():
    """Proxy to the lesson reading exercise generator."""
    from .helpers.reading_helpers import ai_reading_exercise

    return ai_reading_exercise()
