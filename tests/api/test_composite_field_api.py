from urllib import response
import json
import pytest

@pytest.mark.api
def test_composite_field_api(logged_in_admin, test_db_url):

    response = logged_in_admin.post("/api/reference_dicts", json={"name": "test_dicts"})
    assert response.status_code == 201
    item = response.get_json()
    assert item["id"] == 1

    response = logged_in_admin.post("/create_template", data={
        "name": "Composite Field",
        "fields_json": json.dumps([
            {"id": "f1", "type": "composite", "label": "composite field",
             "parts": [{"name": "part1", "type": "number", "label": "ЧИСЛО"},
                       {"name": "part2", "type": "number", "label": "СТИХИ"}]
             },
        ])
    }, follow_redirects=True)
    assert response.status_code == 200

