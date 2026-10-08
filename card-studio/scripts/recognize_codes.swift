import Foundation
import Vision
import AppKit
var output:[String:String]=[:]
for path in CommandLine.arguments.dropFirst() {
 guard let image=NSImage(contentsOfFile:path),let cg=image.cgImage(forProposedRect:nil,context:nil,hints:nil) else {continue}
 let req=VNRecognizeTextRequest();req.recognitionLevel = .accurate;req.recognitionLanguages=["en-US"];req.usesLanguageCorrection=false;req.regionOfInterest=CGRect(x:0,y:0,width:1,height:1)
 do{try VNImageRequestHandler(cgImage:cg).perform([req]);for item in req.results ?? [] {let t=item.topCandidates(1).first?.string ?? "";if let r=t.range(of:"AP[0-9]+[-‐– ][0-9]{3}[A-Z]?",options:.regularExpression){output[path]=String(t[r]).replacingOccurrences(of:" ",with:"-");break}}}catch{}
}
let data=try JSONSerialization.data(withJSONObject:output,options:[.sortedKeys]);print(String(data:data,encoding:.utf8)!)
