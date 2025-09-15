# filepath: /home/droot/medc-img-annotation-app/backend/app/static/images/gen_mongo_insert.py
import os
files = [f for f in os.listdir('.') if f.lower().endswith(('.jpg','.jpeg','.png'))]
print("db.images.insertMany([")
for f in files:
    print(f'  {{"dataset_id": "testset", "filename": "{f}"}},')
print("])")