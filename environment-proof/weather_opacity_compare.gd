extends SceneTree

const CONTEXTS := ["path_eye","elevated_oblique"]
const OUTPUT := "res://weather-opacity-render-comparison.json"

func image_path(prefix:String,context:String)->String:
    return "res://opacity-%s-%s.png" % [prefix,context]

func compare_images(control_path:String,candidate_path:String)->Dictionary:
    var control:=Image.load_from_file(control_path)
    var candidate:=Image.load_from_file(candidate_path)
    if control==null or candidate==null or control.is_empty() or candidate.is_empty():
        return {"state":"FAIL_LOAD"}
    if control.get_width()!=candidate.get_width() or control.get_height()!=candidate.get_height():
        return {"state":"FAIL_DIMENSIONS"}
    var changed:=0
    var darker:=0
    var brighter:=0
    var min_x:=control.get_width()
    var min_y:=control.get_height()
    var max_x:=-1
    var max_y:=-1
    var abs_rgb_sum:=0.0
    for y in range(control.get_height()):
        for x in range(control.get_width()):
            var a:=control.get_pixel(x,y)
            var b:=candidate.get_pixel(x,y)
            if a!=b:
                changed+=1
                min_x=mini(min_x,x)
                min_y=mini(min_y,y)
                max_x=maxi(max_x,x)
                max_y=maxi(max_y,y)
                abs_rgb_sum+=absf(a.r-b.r)+absf(a.g-b.g)+absf(a.b-b.b)
                var la:=a.r*0.2126+a.g*0.7152+a.b*0.0722
                var lb:=b.r*0.2126+b.g*0.7152+b.b*0.0722
                if lb<la:
                    darker+=1
                elif lb>la:
                    brighter+=1
    var pixels:=control.get_width()*control.get_height()
    return {
        "state":"PASS" if changed>0 else "FAIL_NO_VISIBLE_DELTA",
        "width":control.get_width(),
        "height":control.get_height(),
        "pixels":pixels,
        "changed_pixels":changed,
        "changed_fraction":float(changed)/float(pixels),
        "darker_changed_pixels":darker,
        "brighter_changed_pixels":brighter,
        "mean_abs_rgb_delta_per_changed_pixel":abs_rgb_sum/float(changed) if changed>0 else 0.0,
        "changed_bbox":[min_x,min_y,max_x,max_y] if changed>0 else [],
    }

func _initialize()->void:
    var contexts={}
    var all_pass:=true
    for context in CONTEXTS:
        var row:=compare_images(image_path("control",String(context)),image_path("candidate",String(context)))
        contexts[String(context)]=row
        if row.get("state")!="PASS":
            all_pass=false
    var report={
        "schema":"axm.environment-weather-opacity-render-comparison/v0.1",
        "state":"PASS_VISIBLE_SOURCE_OPACITY_DELTA" if all_pass else "FAIL_RENDER_COMPARISON",
        "contexts":contexts,
        "truth_boundary":"Pixel differences prove only that consuming the exact carried per-streak opacity changes the pinned proof-host images. Because control and candidate scene payloads are machine-checked equal except for the render profile, this attributes the retained A/B delta to Weather opacity representation. It is not Art Director acceptance or a physical-atmosphere claim."
    }
    var file:=FileAccess.open(OUTPUT,FileAccess.WRITE)
    if file==null:
        push_error("cannot write Weather opacity comparison")
        quit(1)
        return
    file.store_string(JSON.stringify(report,"  ")+"\n")
    file.close()
    print("AXM WEATHER OPACITY COMPARE ",JSON.stringify(report))
    quit(0 if all_pass else 1)
