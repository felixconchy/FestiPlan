from datetime import datetime
from app.database import Base,SessionLocal,engine
from app.models import Festival,Artist,Stage,Concert,Incident

Base.metadata.create_all(bind=engine)

def dt(v): 
  return datetime.fromisoformat(v)
def seed():
 db=SessionLocal()
 try:
  for model in (Incident,Concert,Stage,Artist,Festival): 
   db.query(model).delete()
  db.commit()
  f=Festival(name="Hellforge Open Air",location="Clisson-sur-Rivière",start_date=dt("2027-06-18T10:00:00"),end_date=dt("2027-06-20T23:59:00"),status="preparation")
  db.add(f); db.commit(); db.refresh(f)
  data=[("Iron Vow","Heavy metal",["large_rigging","special_lighting"]),("Crimson Engine","Thrash metal",["special_lighting"]),("The Last Citadel","Power metal",["large_rigging"]),("Concrete Reign","Hardcore",[]),("Ashes of Tomorrow","Metalcore",["special_lighting"]),("Static Violence","Punk",[]),("Hollow Mountain","Stoner",["special_lighting"]),("Solar Funeral","Doom metal",[]),("Desert Crown","Sludge",[]),("Winter Throne","Black metal",["special_lighting"]),("Nocturnal Veil","Black metal",[]),("Pale Kingdom","Atmospheric metal",["special_lighting"])]
  artists={}
  for n,g,e in data:
   a=Artist(name=n,genre=g,required_equipment=",".join(e)); db.add(a); db.flush(); artists[n]=a
  stage_data=[("Mainstage",50000,["large_rigging","special_lighting","pyrotechnics"]),("Warzone",15000,["special_lighting"]),("Valley",8000,["special_lighting"]),("Temple",10000,["special_lighting"])]
  stages={}
  for n,c,e in stage_data:
   s=Stage(festival_id=f.id,name=n,capacity=c,available_equipment=",".join(e)); db.add(s); db.flush(); stages[n]=s
  db.commit()
  shows=[("Iron Vow","Mainstage","2027-06-18T18:00:00","2027-06-18T19:00:00"),("Crimson Engine","Mainstage","2027-06-18T19:30:00","2027-06-18T20:30:00"),("The Last Citadel","Mainstage","2027-06-18T21:00:00","2027-06-18T22:00:00"),("Concrete Reign","Warzone","2027-06-18T17:00:00","2027-06-18T17:45:00"),("Ashes of Tomorrow","Warzone","2027-06-18T18:15:00","2027-06-18T19:00:00"),("Hollow Mountain","Valley","2027-06-18T19:00:00","2027-06-18T20:00:00"),("Solar Funeral","Valley","2027-06-18T20:30:00","2027-06-18T21:30:00"),("Winter Throne","Temple","2027-06-18T20:00:00","2027-06-18T21:00:00"),("Nocturnal Veil","Temple","2027-06-18T21:30:00","2027-06-18T22:30:00"),("Static Violence","Warzone","2027-06-19T14:00:00","2027-06-19T14:45:00"),("Desert Crown","Valley","2027-06-19T15:00:00","2027-06-19T16:00:00"),("Pale Kingdom","Temple","2027-06-19T16:30:00","2027-06-19T17:30:00"),("Iron Vow","Mainstage","2027-06-19T21:00:00","2027-06-19T22:00:00"),("Crimson Engine","Mainstage","2027-06-20T20:00:00","2027-06-20T21:00:00")]
  for an,sn,st,en in shows:
   db.add(Concert(festival_id=f.id,artist_id=artists[an].id,stage_id=stages[sn].id,start_time=dt(st),end_time=dt(en),status="scheduled"))
  db.commit(); print("Données chargées : Hellforge Open Air, 4 scènes, 12 artistes, 14 concerts.")
 finally: db.close()

if __name__=="__main__": seed()
