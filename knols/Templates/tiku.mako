[
  %for timu in tiku[:-1]:
  {
    "original_text": "${timu['original_text']}", 
    "sources": [
      "${timu['source']}"
    ], 
    "flag": "NA", 
    "ans": "${timu['ans']}", 
    "equations": "NA", 
    "id": "${timu['id']}"
  },
  %endfor
  {
    "original_text": "${tiku[-1]['original_text']}", 
    "sources": [
      "${tiku[-1]['source']}"
    ], 
    "flag": "NA", 
    "ans": "${tiku[-1]['ans']}", 
    "equations": "NA", 
    "id": "${tiku[-1]['id']}"
  }
]