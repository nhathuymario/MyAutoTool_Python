from app.image_finder import find_image_center

def test_find_image():
    result = find_image_center("assets/image/step_1_build.png")
    assert result is not None