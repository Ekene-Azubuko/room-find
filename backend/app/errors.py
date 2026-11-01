from flask import jsonify


def json_http_error(error):
    """Serialize HTTP failures as JSON while retaining protocol headers."""
    response = error.get_response()
    response.data = jsonify({"error": error.description}).data
    response.content_type = "application/json"
    return response
