"""Tests for presentation/slide data models and facade methods."""

from univer.models.slides import Presentation, Shape, Slide


def test_create_presentation():
    pres = Presentation(name="MyDeck")
    assert pres.name == "MyDeck"
    assert pres.id is not None
    assert len(pres.slides) == 0


def test_add_slide():
    pres = Presentation()
    slide = pres.add_slide("Title Slide")
    assert isinstance(slide, Slide)
    assert slide.title == "Title Slide"
    assert len(pres.slides) == 1


def test_get_slide():
    pres = Presentation()
    slide = pres.add_slide()
    assert pres.get_slide(slide.id) is slide
    assert pres.get_slide("nonexistent") is None


def test_slide_add_shape():
    pres = Presentation()
    slide = pres.add_slide()
    shape = slide.add_shape("text", "Hello", x=10, y=20, width=100, height=50)
    assert isinstance(shape, Shape)
    assert shape.text == "Hello"
    assert shape.x == 10
    assert len(slide.shapes) == 1


def test_shape_to_dict():
    shape = Shape(type="image", text="", x=0, y=0, width=200, height=150)
    d = shape.to_dict()
    assert d["type"] == "image"
    assert d["width"] == 200
    assert d["height"] == 150


def test_slide_to_dict():
    pres = Presentation(name="Deck")
    slide = pres.add_slide("Intro")
    slide.add_shape("text", "Welcome", x=0, y=0, width=640, height=480)
    d = slide.to_dict()
    assert d["title"] == "Intro"
    assert len(d["shapes"]) == 1
    assert d["shapes"][0]["text"] == "Welcome"


def test_presentation_to_dict():
    pres = Presentation(name="Deck")
    pres.add_slide("S1")
    pres.add_slide("S2")
    d = pres.to_dict()
    assert d["name"] == "Deck"
    assert len(d["slides"]) == 2


def test_get_shape():
    pres = Presentation()
    slide = pres.add_slide()
    shape = slide.add_shape("text", "x")
    assert slide.get_shape(shape.id) is shape
    assert slide.get_shape("nope") is None
