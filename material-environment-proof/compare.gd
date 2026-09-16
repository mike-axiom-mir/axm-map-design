extends SceneTree

const OUT := "res://material-environment-image-comparison.json"
const CONTEXTS := ["path_eye","elevated_oblique"]

func luma(c:Color)->float:
    return 0.2126*c.r+0.7152*c.g+0.0722*c.b

func compare_images(a:Image,b:Image)->Dictionary:
    if a.get_width()!=b.get_width() or a.get_height()!=b.get_height():
        return {"state":"FAIL_DIMENSIONS"}
    var changed:=0
    var darker:=0
    var brighter:=0
    var max_delta:=0.0
    var luma_abs_sum:=0.0
    var min_x:=a.get_width()
    var min_y:=a.get_height()
    var max_x:=-1
    var max_y:=-1
    for y in range(a.get_height()):
        for x in range(a.get_width()):
            var ca:=a.get_pixel(x,y)
            var cb:=b.get_pixel(x,y)
            var delta:float=maxf(absf(ca.r-cb.r),maxf(absf(ca.g-cb.g),absf(ca.b-cb.b)))
            if delta>(1.0/255.0):
                changed+=1
                max_delta=maxf(max_delta,delta)
                var ld:=luma(cb)-luma(ca)
                luma_abs_sum+=absf(ld)
                if ld<0.0:
                    darker+=1
                elif ld>0.0:
                    brighter+=1
                min_x=mini(min_x,x)
                min_y=mini(min_y,y)
                max_x=maxi(max_x,x)
                max_y=maxi(max_y,y)
    var total:=a.get_width()*a.get_height()
    return {
        "state":"PASS",
        "changed_pixels":changed,
        "total_pixels":total,
        "changed_fraction":float(changed)/float(total),
        "darker_pixels":darker,
        "brighter_pixels":brighter,
        "mean_abs_luma_delta_on_changed":0.0 if changed==0 else luma_abs_sum/float(changed),
        "max_rgb_channel_delta":max_delta,
        "changed_bbox":[] if changed==0 else [min_x,min_y,max_x,max_y]
    }

func _initialize()->void:
    var rows:={}
    for context in CONTEXTS:
        var neutral_path:="res://neutral_%s.png" % context
        var candidate_path:="res://candidate_%s.png" % context
        var neutral:=Image.load_from_file(neutral_path)
        var candidate:=Image.load_from_file(candidate_path)
        if neutral==null or neutral.is_empty() or candidate==null or candidate.is_empty():
            push_error("missing comparison image for %s" % context)
            quit(1)
            return
        var row:=compare_images(neutral,candidate)
        if row.get("state")!="PASS" or int(row["changed_pixels"])<=0:
            push_error("no visible material delta for %s" % context)
            quit(1)
            return
        rows[context]=row
    var receipt={
        "schema":"axm.environment-building-material-image-comparison/v0.1",
        "state":"PASS_VISIBLE_BUILDING_SURFACE_DELTA",
        "contexts":rows,
        "truth_boundary":"Pixel differences prove the exact receiving-scene material candidate changes the retained target-host images. They do not establish aesthetic acceptance, material realism, final lighting or runtime acceptance."
    }
    var file:=FileAccess.open(OUT,FileAccess.WRITE)
    file.store_string(JSON.stringify(receipt,"  ")+"\n")
    file.close()
    print("AXM BUILDING MATERIAL IMAGE COMPARISON ",JSON.stringify(receipt))
    quit(0)
