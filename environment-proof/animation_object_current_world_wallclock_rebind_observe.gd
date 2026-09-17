extends "res://atmosphere_current_world_object_motion_observe.gd"

func _initialize()->void:
    var predecessor := load("res://animation_object_current_world_wallclock_observe.gd")
    if predecessor == null:
        push_error("Animation diagnostic could not load predecessor wall-clock observer")
        quit(1)
        return
    push_error("Animation diagnostic unexpectedly loaded predecessor wall-clock observer; restore rebind implementation")
    quit(1)
