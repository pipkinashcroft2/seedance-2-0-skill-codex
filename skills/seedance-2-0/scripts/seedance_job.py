import argparse,json,os
from urllib.request import Request
MODELS={"seedance-2.0-mini","seedance-2.0-fast","seedance-2.0"}
def build(model,prompt,duration=5,resolution="720p",aspect_ratio="16:9"):
 if model not in MODELS: raise ValueError("unknown Seedance 2.0 variant")
 if not isinstance(duration,int): raise TypeError("duration must be an integer")
 if not 4<=duration<=15: raise ValueError("duration must be 4..15; check the selected page")
 if not prompt.strip(): raise ValueError("prompt is required")
 return {"model":model,"prompt":prompt,"duration":duration,"resolution":resolution,"aspect_ratio":aspect_ratio}
def request_preview(body,base="https://argolink.io/v1"):
 key=os.getenv("SEEDANCE_API_KEY")
 if not key: raise RuntimeError("set SEEDANCE_API_KEY")
 return Request(base.rstrip("/")+"/videos/generations",data=json.dumps(body).encode(),headers={"Authorization":"Bearer "+key,"Content-Type":"application/json","User-Agent":"seedance-2-0-skill/1.0"})
def main():
 p=argparse.ArgumentParser();p.add_argument("--model",default="seedance-2.0-mini");p.add_argument("--prompt",required=True);p.add_argument("--duration",type=int,default=5);p.add_argument("--print-json",action="store_true");a=p.parse_args(); body=build(a.model,a.prompt,a.duration); print(json.dumps(body) if a.print_json else request_preview(body).full_url)
if __name__=="__main__":main()
