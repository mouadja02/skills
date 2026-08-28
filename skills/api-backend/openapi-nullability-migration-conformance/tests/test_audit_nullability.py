import importlib.util, io, json, os, tempfile, unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
P=Path(__file__).parents[1]/"scripts"/"audit_nullability.py"
S=importlib.util.spec_from_file_location("audit_nullability",P); M=importlib.util.module_from_spec(S); S.loader.exec_module(M)

class Tests(unittest.TestCase):
 def base(self,version="3.0.3",schema=None): return {"openapi":version,"components":{"schemas":{"X":schema or {"type":"object"}}}}
 def codes(self,d): return {x["code"] for x in M.audit(d)["findings"]}
 def test_required_and_nullable_are_independent(self):
  d=self.base(schema={"type":"object","required":["a"],"properties":{"a":{"type":"string","nullable":True},"b":{"type":"string"}}})
  r=M.audit(d); st={x["pointer"]:x for x in r["property_states"]}
  self.assertEqual((st["#/components/schemas/X/properties/a"]["missing_allowed"],st["#/components/schemas/X/properties/a"]["null_allowed"]),(False,True))
  self.assertEqual((st["#/components/schemas/X/properties/b"]["missing_allowed"],st["#/components/schemas/X/properties/b"]["null_allowed"]),(True,False))
 def test_oas30_ref_sibling_and_composition(self):
  d=self.base(schema={"type":"object","properties":{"bad":{"$ref":"#/components/schemas/X","nullable":True},"uncertain":{"nullable":True,"allOf":[{"$ref":"#/components/schemas/X"}]}}})
  self.assertEqual(self.codes(d),{"NULLABLE_REF_SIBLING_IGNORED","NULLABLE_WITHOUT_LOCAL_TYPE"})
 def test_oas31_union_and_legacy_keyword(self):
  good=self.base("3.1.0",{"type":"object","required":["a"],"properties":{"a":{"type":["string","null"]}}})
  self.assertFalse(self.codes(good)); self.assertTrue(M.audit(good)["property_states"][0]["null_allowed"])
  bad=self.base("3.1.0",{"type":"string","nullable":True}); self.assertIn("NULLABLE_KEYWORD_OAS31",self.codes(bad))
 def test_enum_null_requires_null_type(self): self.assertIn("ENUM_NULL_WITHOUT_NULL_TYPE",self.codes(self.base(schema={"type":"string","enum":["ok",None]})))
 def test_inline_operation_schema_is_inventoried_once(self):
  d={"openapi":"3.0.3","paths":{"/x":{"get":{"responses":{"200":{"description":"ok","content":{"application/json":{"schema":{"type":"object","required":["schema"],"properties":{"schema":{"type":"string","nullable":True}}}}}}}}}}}
  r=M.audit(d); states=[x for x in r["property_states"] if x["pointer"].endswith("/properties/schema")]
  self.assertEqual(len(states),1); self.assertTrue(states[0]["required"]); self.assertTrue(states[0]["null_allowed"])
 def test_type_and_required_shapes_fail_closed(self):
  d=self.base("3.1.0",{"type":["string","string"],"required":[1],"properties":[]})
  self.assertTrue({"TYPE_ARRAY_INVALID","REQUIRED_INVALID","PROPERTIES_INVALID"} <= self.codes(d))
 def test_top_level_and_nonfinite_rejected(self):
  with self.assertRaises(ValueError): M.audit([])
  with self.assertRaises(ValueError): M.audit({"openapi":"3.1.0","x":float("nan")})
 def run_file(self,raw):
  with tempfile.NamedTemporaryFile("w",delete=False,encoding="utf-8") as f: f.write(raw); p=f.name
  try:
   out,err=io.StringIO(),io.StringIO()
   with redirect_stdout(out),redirect_stderr(err): rc=M.main([p])
   return rc,out.getvalue(),err.getvalue()
  finally: os.unlink(p)
 def test_malformed_json_and_nan_exit_2(self):
  self.assertEqual(self.run_file("{")[0],2); self.assertEqual(self.run_file('{"openapi":"3.1.0","x":NaN}')[0],2)
 def test_cli_exit_and_no_modification(self):
  d=self.base(); rc,out,err=self.run_file(json.dumps(d)); self.assertEqual(rc,0); self.assertFalse(json.loads(out)["modified"]); self.assertEqual(err,"")
 def test_broken_stdout_exit_3(self):
  d=self.base()
  with tempfile.NamedTemporaryFile("w",delete=False) as f: json.dump(d,f); p=f.name
  class Broken:
   def write(self,*a): raise OSError("closed")
   def flush(self): pass
  old=M.sys.stdout; M.sys.stdout=Broken()
  try: self.assertEqual(M.main([p]),3)
  finally: M.sys.stdout=old; os.unlink(p)
if __name__=="__main__": unittest.main()
