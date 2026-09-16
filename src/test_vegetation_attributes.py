from dbfread import DBF


DBF_PATH = (
    "/Users/ayubgurung/Downloads/"
    "SVTM_NSW_Extant_PCT_vC2_0_M2_2_108/"
    "SVTM_NSW_Extant_PCT_vC2_0_M2_2_5m.tif.vat.dbf"
)


table = DBF(
    DBF_PATH,
    load=True,
    encoding="cp1252"

)

print("Fields:")
print(table.field_names)

print("\nFirst 5 records:")

for index, record in enumerate(table):

    print(record)

    if index == 4:
        break