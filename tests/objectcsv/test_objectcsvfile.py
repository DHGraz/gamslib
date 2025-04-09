from pathlib import Path
from gamslib.objectcsv.objectcsvfile import ObjectCSVFile
from gamslib.objectcsv.objectdata import ObjectData


def test_objectcsvfile(objcsvfile: Path, objdata: ObjectData):
    "Should create an ObjectCSVFile object from a csv file."
    ocf = ObjectCSVFile.from_csv(objcsvfile)
    result = list(ocf.get_data())
    assert len(result) == 1
    assert result[0] == objdata

    # test the get_data method with pid parameter, which should return the same result,
    # because we only have one object in the csv file
    result = list(ocf.get_data("obj1"))
    assert len(result) == 1
    assert result[0] == objdata

    # and the __len__method
    assert len(ocf) == 1

    # now save the object to a new csv file and compare the content
    csv_file = objcsvfile.parent / "object2.csv"
    ocf.to_csv(csv_file)
    assert objcsvfile.read_text() == csv_file.read_text()
