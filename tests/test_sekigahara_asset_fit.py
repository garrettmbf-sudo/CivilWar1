import importlib.util
from pathlib import Path
from PIL import Image, ImageDraw

spec=importlib.util.spec_from_file_location('import_kit',
    Path(__file__).parents[1]/'tools/sekigahara_valley/build_import_kit.py')
kit=importlib.util.module_from_spec(spec);spec.loader.exec_module(kit)


def test_tall_subject_preserves_both_ends_with_margin(tmp_path):
    source=Image.new('RGBA',(80,240))
    draw=ImageDraw.Draw(source)
    draw.rectangle((28,2,52,238),fill='blue')
    draw.rectangle((28,2,52,9),fill='red')
    draw.rectangle((28,231,52,238),fill='yellow')
    path=tmp_path/'subject.png';source.save(path)
    image,record=kit.fit_art(path)
    assert image.size==(704,608)
    assert record['original_alpha_bbox']==[28,2,53,239]
    x0,y0,x1,y1=record['fitted_alpha_bbox']
    assert x0>0 and y0>0 and x1<704 and y1<608
    pixels=list(image.getdata())
    assert any(r>220 and g<40 and b<40 and a>200 for r,g,b,a in pixels)
    assert any(r>220 and g>220 and b<40 and a>200 for r,g,b,a in pixels)


def test_wide_subject_fits_exact_image_layer_ratio(tmp_path):
    source=Image.new('RGBA',(300,80),'green')
    path=tmp_path/'gun.png';source.save(path)
    image,record=kit.fit_art(path)
    assert image.width/image.height==22/19
    x0,y0,x1,y1=record['fitted_alpha_bbox']
    assert x1-x0<=576 and y1-y0<=480
