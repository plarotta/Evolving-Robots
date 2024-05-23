'''wrappers to display simulation data using vpython'''

import time
from vpython import *
import pickle
import sys
import os
sys.path.append(os.getcwd())
from simulate.fast_utils import get_COM_fast, get_spring_l_fast
import pysim


def initialize_scene(z):
    # walls
    scene = canvas(width=1200,height=750,background=color.black)
    v = wtext(text="0 m/s")  
    floor = box(pos=vector(0.5,z-0.06,0), height=0.02, length=100, width=100,color=color.white)
    for x in range(-50,53,3):
        gridx = curve(pos=[vector(x,z-0.06,50),vector(x,z-0.06,-50)],color=color.black)
    for y in range(-50,53,3):
        gridx = curve(pos=[vector(50,z-0.06,y),vector(-50,z-0.06,y)],color=color.black)

def plot(masses):
    m_plots = []
    
    for mass in masses:
        m_temp = sphere(pos=vector(mass[0][0],mass[0][1],mass[0][2]), 
                        radius=0.06, 
                        color=color.green)
        m_plots.append(m_temp)
    COM_pos = get_COM_fast(masses)
    
    COM = sphere(pos=vector(COM_pos[0],COM_pos[1],COM_pos[2]), radius=0.06, color=color.yellow)
    scene.camera.follow(COM)

def plot_springs(springs, masses):
    # s_plots = []
    for spring in springs:
        m1_pos = masses[int(spring[0][0])][0]
        m2_pos = masses[int(spring[0][1])][0]
        s_temp = cylinder(pos=vector(m1_pos[0], m1_pos[1], m1_pos[2]), 
                          axis=vector(m2_pos[0]-m1_pos[0], m2_pos[1]-m1_pos[1], m2_pos[2]-m1_pos[2]), 
                          length=get_spring_l_fast(masses,spring),
                          color=color.red, 
                          radius=0.01)
        # s_plots.append(s_temp)
    
    
    # return(m_plots,s_plots,COM,v)

def plot_robot_masses(robot_masses, offset_x=0,offset_z=0):
    mass_plots = []
    for mass in robot_masses:
        m_temp = sphere(pos=vector(mass[0]+offset_x,mass[1],mass[2]+offset_z), 
                        radius=0.06, 
                        color=color.green)
        mass_plots.append(m_temp)
    COM_pos = get_COM_fast(robot_masses)
    COM_plots = sphere(pos=vector(COM_pos[0],COM_pos[1],COM_pos[2]), radius=0.06, color=color.yellow)
    return(mass_plots, COM_plots)

def plot_robot_springs(robot_springs, robot_masses, offset_x=0, offset_y=0):
    s_plots = []
    for spring in robot_springs:
        m1_pos = robot_masses[int(spring[0])][0:3]
        m2_pos = robot_masses[int(spring[1])][0:3]
        s_temp = cylinder(pos=vector(m1_pos[0], m1_pos[1], m1_pos[2]), 
                          axis=vector(m2_pos[0]-m1_pos[0], m2_pos[1]-m1_pos[1], m2_pos[2]-m1_pos[2]), 
                          length=get_spring_l_fast(robot_masses,spring),
                          color=color.red, 
                          radius=0.01)
        s_plots.append(s_temp)


def update_scene(masses, springs, m_plots, s_plots, COM,v,speed):
    for idx,m in enumerate(m_plots):
        m.pos = vector(masses[idx][0][0], masses[idx][0][1], masses[idx][0][2])
    
    for idx,s in enumerate(s_plots):
        m1_pos = masses[int(springs[idx][0][0])][0]
        m2_pos = masses[int(springs[idx][0][1])][0]
        s.pos = vector(m1_pos[0], m1_pos[1], m1_pos[2])
        s.axis = vector(m2_pos[0]-m1_pos[0], m2_pos[1]-m1_pos[1], m2_pos[2]-m1_pos[2])
        s.length= get_spring_l_fast(masses,springs[idx])
    COM_pos = get_COM_fast(masses)
    COM.pos = vector(COM_pos[0],COM_pos[1],COM_pos[2])
    v.text = str(str(round(speed,3))+" m/s")

def visualize_simulation(path_to_sim,floor):
    time.sleep(6)
    with open(path_to_sim, 'rb') as handle:
        sim_logger = pickle.load(handle)
    
    timestamps = sorted(list(sim_logger.keys()))
    m_obs, s_obs, COM,v = initialize_scene(sim_logger[timestamps[0]]['masses'], 
                                           sim_logger[timestamps[0]]['springs'],
                                           z=floor-0.06)
    for i,t in enumerate(timestamps[1:]):
        print(f'sim time: {t:.2f}')
        rate(50)
        update_scene(sim_logger[timestamps[i]]['masses'], 
                     sim_logger[timestamps[i]]['springs'], 
                     m_obs, 
                     s_obs, 
                     COM,
                     v,
                     sim_logger[timestamps[i]]['speed'])

if __name__ == "__main__":
    
    # from simulate.fast_utils import *
    # from simulate.simulation import *
    simy = pysim.Simulation()
    initialize_scene(0)
    plot_robot_masses(simy.get_sim_masses()[0])
    plot_robot_springs(simy.get_sim_springs()[0], simy.get_sim_masses()[0])

    
    # a = Simulation()
    # sim_path = a.run_simulation(sim_length=20, time_step=0.001, log_k=5, mu_s=0.5, mu_k=0.3, floor_z_position=-4, save=True)
    # visualize_simulation(sim_path, floor=-4)