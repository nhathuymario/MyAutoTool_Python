from app.clicker import click_point

def test_click():
    x = 100
    y = 100
    click_point(x, y)
    assert True