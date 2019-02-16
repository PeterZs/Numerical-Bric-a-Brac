"""
@author: Vincent Bonnet
@description : example scenes for unit testing
"""

import objects
import core
import math
import system.setup.commands as cmds

'''
 Global Constants
'''
WIRE_ROOT_POS = [0.0, 2.0] # in meters
WIRE_END_POS = [0.0, -2.0] # in meters
WIRE_NUM_SEGMENTS = 30

BEAM_POS = [-4.0, 0.0] # in meters
BEAM_WIDTH = 8.0 # in meters
BEAM_HEIGHT = 1.0 # in meters
BEAM_CELL_X = 6 # number of cells along x
BEAM_CELL_Y = 4 # number of cells along y

PARTICLE_MASS = 0.001 # in Kg

GRAVITY = (0.0, -9.81) # in meters per second^2


def init_multi_wire_scene(scene, context):
    '''
    Initalizes a scene with a wire attached to a kinematic object
    '''
    # wire shape
    wire_shapes = []
    for i in range(6):
        x = -2.0 + (i * 0.25)
        wire_shape = core.WireShape([x, 1.5], [x, -1.5] , WIRE_NUM_SEGMENTS)
        wire_shapes.append(wire_shape)

    # anchor shape and animation
    moving_anchor_shape = core.RectangleShape(min_x = -2.0, min_y = 1.5,
                                              max_x = 0.0, max_y =2.0)
    moving_anchor_position, moving_anchor_rotation = cmds.extract_transform_from_shape(moving_anchor_shape)
    func = lambda time: [[moving_anchor_position[0] + time,
                          moving_anchor_position[1]], 0.0]

    moving_anchor_animator = objects.Animator(func, context)

    # collider shape
    collider_shape = core.RectangleShape(WIRE_ROOT_POS[0], WIRE_ROOT_POS[1] - 3,
                                       WIRE_ROOT_POS[0] + 0.5, WIRE_ROOT_POS[1] - 2)
    collider_position, collider_rotation = cmds.extract_transform_from_shape(moving_anchor_shape)
    collider_rotation = 45.

    # Populate Scene with data and conditions
    moving_anchor = cmds.add_kinematic(scene, moving_anchor_shape,
                                                moving_anchor_position,
                                                moving_anchor_rotation,
                                                moving_anchor_animator)

    collider = cmds.add_kinematic(scene, collider_shape,
                                           collider_position,
                                           collider_rotation)

    for wire_shape in wire_shapes:
        wire = cmds.add_dynamic(scene, wire_shape, PARTICLE_MASS)
        edge_condiction = cmds.add_edge_constraint(scene, wire, stiffness=100.0, damping=0.0)
        wire_bending_condition = cmds.add_wire_bending_constraint(scene, wire, stiffness=0.2, damping=0.0)
        cmds.add_kinematic_attachment(scene, wire, moving_anchor, stiffness=100.0, damping=0.0, distance=0.1)
        cmds.add_kinematic_collision(scene, wire, collider, stiffness=1000.0, damping=0.0)
        cmds.add_gravity_acceleration(scene, GRAVITY)

        # Add Metadata to visualize the data and constraints
        cmds.add_render_prefs(wire, ['co', 1])
        cmds.add_render_prefs(edge_condiction, ['m-', 1])
        cmds.add_render_prefs(wire_bending_condition, ['m-', 1])


def init_wire_example(bundle):
    '''
    Initalizes a scene with a wire attached to a kinematic object
    '''
    # wire shape
    wire_shape = core.WireShape(WIRE_ROOT_POS, WIRE_END_POS, WIRE_NUM_SEGMENTS)

    # collider shape
    collider_shape = core.RectangleShape(WIRE_ROOT_POS[0], WIRE_ROOT_POS[1] - 3,
                                       WIRE_ROOT_POS[0] + 0.5, WIRE_ROOT_POS[1] - 2)

    # anchor shape and animation
    moving_anchor_shape = core.RectangleShape(WIRE_ROOT_POS[0], WIRE_ROOT_POS[1] - 0.5,
                                              WIRE_ROOT_POS[0] + 0.25, WIRE_ROOT_POS[1])

    moving_anchor_position, moving_anchor_rotation = cmds.extract_transform_from_shape(moving_anchor_shape)
    decay_rate = 0.5
    func = lambda time: [[moving_anchor_position[0] + math.sin(time * 10.0) * math.pow(1.0-decay_rate, time),
                          moving_anchor_position[1]], math.sin(time * 10.0) * 90.0 * math.pow(1.0-decay_rate, time)]
    moving_anchor_animator = objects.Animator(func, bundle.context())

    # Populate scene with commands
    wire_handle = bundle.run('add_dynamic', wire_shape, PARTICLE_MASS)
    collider_handle = bundle.run('add_kinematic', collider_shape)
    moving_anchor_handle = bundle.run('add_kinematic', moving_anchor_shape,
                                                          moving_anchor_position,
                                                          moving_anchor_rotation,
                                                          moving_anchor_animator)

    edge_condition_handle = bundle.run('add_edge_constraint', wire_handle, 100.0, 0.0)
    bundle.run('add_wire_bending_constraint', wire_handle, 0.2, 0.0)
    bundle.run('add_kinematic_attachment', wire_handle, moving_anchor_handle, 100.0, 0.0, 0.1)
    bundle.run('add_kinematic_collision', wire_handle, collider_handle, 1000.0, 0.0)
    bundle.run('add_gravity_acceleration', GRAVITY)

    bundle.run('add_render_prefs', wire_handle, ['co', 1])
    bundle.run('add_render_prefs', edge_condition_handle, ['m-', 1])

def init_beam_scene(scene, context):
    '''
    Initalizes a scene with a beam and a wire
    '''
    # beam shape
    beam_shape = core.BeamShape(BEAM_POS, BEAM_WIDTH, BEAM_HEIGHT, BEAM_CELL_X, BEAM_CELL_Y)

    # wire shape
    wire_start_pos = [BEAM_POS[0], BEAM_POS[1] + BEAM_HEIGHT]
    wire_end_pos = [BEAM_POS[0] + BEAM_WIDTH, BEAM_POS[1] + BEAM_HEIGHT]
    wire_shape = core.WireShape(wire_start_pos, wire_end_pos, BEAM_CELL_X * 8)

    # left anchor shape and animation
    left_anchor_shape = core.RectangleShape(BEAM_POS[0] - 0.5, BEAM_POS[1],
                                            BEAM_POS[0], BEAM_POS[1] + BEAM_HEIGHT)
    l_pos, l_rot = cmds.extract_transform_from_shape(left_anchor_shape)
    func = lambda time: [[l_pos[0] + math.sin(2.0 * time) * 0.1, l_pos[1] + math.sin(time * 4.0)], l_rot]
    l_animator = objects.Animator(func, context)

    # right anchor shape and animation
    right_anchor_shape = core.RectangleShape(BEAM_POS[0] + BEAM_WIDTH, BEAM_POS[1],
                                             BEAM_POS[0] + BEAM_WIDTH + 0.5, BEAM_POS[1] + BEAM_HEIGHT)
    r_pos, r_rot = cmds.extract_transform_from_shape(right_anchor_shape)
    func = lambda time: [[r_pos[0] + math.sin(2.0 * time) * -0.1, r_pos[1]], r_rot]
    r_animator = objects.Animator(func, context)

    # Populate Scene with data and conditions
    beam = cmds.add_dynamic(scene, beam_shape, PARTICLE_MASS)
    wire = cmds.add_dynamic(scene, wire_shape, PARTICLE_MASS)
    left_anchor = cmds.add_kinematic(scene, left_anchor_shape, l_pos, l_rot, l_animator)
    right_anchor = cmds.add_kinematic(scene, right_anchor_shape, r_pos, r_rot, r_animator)

    wire_edge_condition = cmds.add_edge_constraint(scene, wire, stiffness=10.0, damping=0.0)
    beam_edge_condition = cmds.add_edge_constraint(scene, beam, stiffness=20.0, damping=0.0)
    cmds.add_face_constraint(scene, beam, stiffness=20.0, damping=0.0)
    cmds.add_kinematic_attachment(scene, beam, right_anchor, stiffness=100.0, damping=0.0, distance=0.1)
    cmds.add_kinematic_attachment(scene, beam, left_anchor, stiffness=100.0, damping=0.0, distance=0.1)
    cmds.add_dynamic_attachment(scene, beam, wire, stiffness=100.0, damping=0.0, distance=0.001)
    cmds.add_gravity_acceleration(scene, GRAVITY)

    # Add Metadata
    cmds.add_render_prefs(beam, ['go', 1])
    cmds.add_render_prefs(beam_edge_condition, ['k-', 1])

    cmds.add_render_prefs(wire, ['co', 1])
    cmds.add_render_prefs(wire_edge_condition, ['m-', 1])

