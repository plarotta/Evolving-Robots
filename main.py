import time
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from vpython import *
import secrets
import random
import copy
import pickle
from numba import njit, vectorize, jit
import cProfile, pstats
import re

    


# mass is going to become a 5x3 np array
# mass = np.array(
#                   
#                   np.array([0,0,0]), {current position}
#                   np.array([0,0,0]), {velocity}
#                   np.array([0,0,0]), {acceleration}
#                   np.array([0,0,0]),  {net force}
#                   np.array([0,0,0]), {initial position}
# )

# spring is going to become a 3x2 np array
# spring = np.array(
#                   np.array([m1_idx, m2_idx, 0,0]),
#                   np.array([a,b,c,k])  {a = rest length, b = sinusoid amplitude, c = sinusoid phase shift, k = spring constant}
# )

# @njit()
def initialize_masses():
    masses = np.zeros(120).reshape(8,5,3)
    n = 0
    for x in [0,1]:
        for y in [0,1]:
            for z in [0,1]:
                masses[n][0] = np.array([float(x),float(y),float(z)])
                masses[n][4] = np.array([float(x),float(y),float(z)])
                n+=1
    return(masses)

# @njit()
def initialize_springs(masses):
    first = True
    for mass_idx1 in range(len(masses)):
        for mass_idx2 in range(mass_idx1+1,len(masses)):
            m1_p = masses[mass_idx1][0] #get pos
            m2_p = masses[mass_idx2][0] #get pos
            length = np.linalg.norm(m2_p-m1_p)
            # print(length)
            if first == True:
                springs = np.array([[[mass_idx1, mass_idx2, 0, 0],[length, 0,0,5000]]])
                first = False
            else:
                springs = np.concatenate((springs, np.array([[[mass_idx1, mass_idx2, 0, 0],[length, 0,0,5000]]])))
    return(springs)
    
@njit()
def interact_fast(springs,masses,t,increment,mu_static,mu_kinetic,floor=-4,breath=False):
    for s in springs:
        l = get_spring_l(masses,s)
        l_vect = masses[int(s[0][1])][0] - masses[int(s[0][0])][0]  
        L0 = s[1][0] + s[1][1] * np.sin(4*t + s[1][2])
        f_k = s[1][3] * (l - L0)
        f_dir = f_k/np.sqrt(l_vect[0]**2 + l_vect[1]**2 + l_vect[2]**2)
        f_full = f_dir * l_vect
        masses[int(s[0][0])][3] = masses[int(s[0][0])][3] + f_full
        masses[int(s[0][1])][3] = masses[int(s[0][1])][3] - f_full
    for m in masses:   
        m[3] = m[3] + np.array([0,-9.81,0]) #gravity
        if m[0][1] <= floor:
            f_net = m[3]
            Fp = np.array([f_net[0], 0.0, f_net[2]])
            Fp_norm = np.sqrt(Fp[0]**2 + Fp[2]**2)
            Fn = np.array([0.0, f_net[1], 0.0])
            Fn_norm = f_net[1]
            if Fp_norm < abs(Fn_norm * mu_static): #friction
                m[3] = m[3] - np.array([f_net[0],0.0,f_net[2]])                

            else:
                dirFn = mu_kinetic*Fn_norm*np.array([f_net[0], 0.0, f_net[2]])/Fp_norm #friction
                m[3] = m[3] - np.array([dirFn[0],0.0,dirFn[2]])

            if m[0][1] < floor:
                ry = 10000*(abs(m[0][1] - floor))
                m[3] = m[3] + np.array([0,ry,0])
        integrate(m,increment)

def interact(springs,masses,t,increment,mu_static,mu_kinetic,floor=-4,breath=False):
    for s in springs:
        l = get_spring_l(masses,s)
        l_vect = masses[int(s[0][1])][0] - masses[int(s[0][0])][0]  
        L0 = s[1][0] + s[1][1] * np.sin(2*t + s[1][2])
        f_k = s[1][3] * (l - L0)
        
        f_dir = f_k/np.sqrt(l_vect[0]**2 + l_vect[1]**2 + l_vect[2]**2)
        f_full = f_dir * l_vect
        masses[int(s[0][0])][3] = masses[int(s[0][0])][3] + f_full
        masses[int(s[0][1])][3] = masses[int(s[0][1])][3] - f_full
    for m in masses:   
        m[3] = m[3] + np.array([0,-9.81,0]) #gravity
        if m[0][1] <= floor:
            
            f_net = m[3]
            Fp = np.array([f_net[0], 0.0, f_net[2]])
            Fp_norm = np.sqrt(Fp[0]**2 + Fp[2]**2)
            Fn = np.array([0.0, f_net[1], 0.0])
            Fn_norm = f_net[1]
            if Fp_norm < Fn_norm * mu_static: #friction
                m[3] = m[3] - np.array([f_net[0],0.0,f_net[2]])                

            else:
                try:
                    dirFn = mu_kinetic*Fn_norm*np.array([f_net[0], 0.0, f_net[2]])/Fp_norm #friction
                except ZeroDivisionError:
                    print(m)
                    print("sjsndjsn")
                    raise ValueError
                m[3] = m[3] - np.array([dirFn[0],0.0,dirFn[2]])

            if m[0][1] < floor:
                ry = 10000*(abs(m[0][1] - floor))
                m[3] = m[3] + np.array([0,ry,0])
        integrate(m,increment)

@njit()
def integrate(mass,increment):
    mass[2] = mass[3]/0.1
    mass[1] = mass[1] + mass[2]*increment
    mass[1] = mass[1] * 0.9985
    mass[0] = mass[0] + mass[1]*increment
    mass[3] = np.array([0.0,0.0,0.0])

    
@njit()
def get_spring_l(masses, spring):
    m1_idx1 = spring[0][0]
    m2_idx2 = spring[0][1]
    m1_p = masses[int(m1_idx1)][0]
    m2_p = masses[int(m2_idx2)][0]
    diff = m2_p-m1_p
    return(np.sqrt(diff[0]**2 + diff[1]**2 + diff[2]**2))
        
def initialize_scene(masses,springs,z, breath=False):
    # walls
    if not breath:
        floor = box(pos=vector(0.5,z-0.06,0), height=0.02, length=100, width=100,color=color.white)
    m_plots = []
    for mass in masses:
        m_temp = sphere(pos=vector(mass[0][0],mass[0][1],mass[0][2]), radius=0.06, color=color.green)
        m_plots.append(m_temp)
    s_plots = []
    for spring in springs:
        m1_pos = masses[int(spring[0][0])][0]
        m2_pos = masses[int(spring[0][1])][0]
        s_temp = cylinder(pos=vector(m1_pos[0], m1_pos[1], m1_pos[2]), axis=vector(m2_pos[0]-m1_pos[0], m2_pos[1]-m1_pos[1], m2_pos[2]-m1_pos[2]), length=get_spring_l(masses,spring),color=color.red, radius=0.01)
        s_plots.append(s_temp)
    COM_pos = get_COM(masses)
    COM = sphere(pos=vector(COM_pos[0],COM_pos[1],COM_pos[2]), radius=0.06, color=color.yellow)
    return(m_plots,s_plots,COM)

def update_scene(masses, springs, m_plots, s_plots, COM):
    for idx,m in enumerate(m_plots):
        m.pos = vector(masses[idx][0][0], masses[idx][0][1], masses[idx][0][2])
    
    for idx,s in enumerate(s_plots):
        m1_pos = masses[int(springs[idx][0][0])][0]
        m2_pos = masses[int(springs[idx][0][1])][0]
        s.pos = vector(m1_pos[0], m1_pos[1], m1_pos[2])
        s.axis = vector(m2_pos[0]-m1_pos[0], m2_pos[1]-m1_pos[1], m2_pos[2]-m1_pos[2])
        s.length= get_spring_l(masses,springs[idx])
    COM_pos = get_COM(masses)
    COM.pos = vector(COM_pos[0],COM_pos[1],COM_pos[2])

def run_simulation(masses, springs,final_T,increment, mu_static, mu_kinetic,floor,plot_energies=False, debug_mode = False):
    if debug_mode:
        masses = initialize_masses()
        springs = initialize_springs(masses)
    # masses[0][3] = np.array([300000,600000,400000])
    m_obs, s_obs, COM = initialize_scene(masses, springs,z=floor-0.06)
    
    time.sleep(3)
    
    times = np.arange(0, final_T, 0.02)
    if plot_energies:
        energies = {"springs": [], "masses": []}
    for t in np.arange(0, final_T, increment):
        interact(springs,masses,t,increment, mu_static,mu_kinetic,floor)
        
        if t in times:
            print(t)
            rate(50)
            update_scene(masses, springs,m_obs, s_obs, COM)
    if plot_energies:
        plot_energies(energies)
# @njit()
def get_COM(masses):
    M = sum([0.1 for m in masses])
    masses[:,0,0]
    COMx = np.sum(masses[:,0,0]*0.1)/M
    COMy = np.sum(masses[:,0,1]*0.1)/M
    COMz = np.sum(masses[:,0,2]*0.1)/M
    return(np.array([COMx, COMy, COMz]))

def eval_springs(masses,springs,spring_constants,final_T=3,increment=0.0002, render = False):
    start = time.time()
    print("call to eval")
    for idx in range(len(springs)):
        springs[idx][1][1] = spring_constants[idx][0]
        springs[idx][1][2] = spring_constants[idx][1]
        springs[idx][1][3] = spring_constants[idx][2]
    if render:
        run_simulation(masses, springs,6,0.0002,0.9,0.8,0)
    else:
        p1 = get_COM(masses)
        for t in np.arange(0, final_T, increment):
            interact_fast(springs,masses,t,increment,0.9,0.8,floor=0)
        p2 = get_COM(masses)
        print("eval time: ", time.time()-start)
        rehome(masses) #reset current state of the masses
        return(np.linalg.norm(np.array([p2[0],0,p2[2]])-np.array([p1[0],0,p1[2]])))

def rehome(masses):
    for m in masses:
        pos0 = m[4]
        m[0] = pos0
        m[1] = np.array([0.0, 0.0, 0.0])
        m[2] = np.array([0.0, 0.0, 0.0])
        m[3] = np.array([0.0, 0.0, 0.0])
    
def evolve_robot(n_gen):
    '''
    Encoding: 
    [
        [b1,c1,k1], spring 1 params
        [b2,c2,k2], spring 2 params
        [b3,c3,k3], spring 3 params
        [b4,c4,k4] spring 4 params
    ] 

    Mutation:
    -choose random spring
    -change the value of each of its params by some delta. different delta for each param

    Selection:
    -rank-based

    Crossover:
    *two-point crossover*
    -choose n1 and n2
    -child1: for 0 to n1 parent1.springs[0:n1]=parent2.springs[0:n1], 
             for n1 to n2 pass
             for n2 to end parent1.springs[n1:n2]=parent2.springs[n1:n2]
    -child2: complement of child2
    
    '''
    pop_size = 10
    mut_rate = .7
    masses = initialize_masses()
    springs = initialize_springs(masses)
    population_pool = initialize_population(pop_size,springs)
   
    
    pool_springs = []
    for idx in range(len(population_pool)):
        pool_springs.append(springs)
    pool_masses = []
    for idx in range(len(population_pool)):
        pool_masses.append(masses)   

    for idx in range(len(population_pool)):
        # print("ngen: ", len(next_gen))
        m,s,c = mutate_morphology(pool_masses[idx], pool_springs[idx], population_pool[idx])
        pool_masses[idx] = m
        pool_springs[idx] = s
        population_pool[idx] = c
    
    fits = [eval_springs(pool_masses[i],pool_springs[i],population_pool[i]) for i in range(len(population_pool))]
    arginds = np.argsort(fits)
    population_pool = [population_pool[i] for i in arginds]
    population_pool = list(reversed(population_pool))
    pool_masses = [pool_masses[i] for i in arginds]
    pool_masses = list(reversed(pool_masses))
    pool_springs = [pool_springs[i] for i in arginds]
    pool_springs = list(reversed(pool_springs))

    

    next_gen = []
    next_masses = []
    next_springs = []
    best_fits = []
    n = 0



    for i in range(n_gen):
        print("Began generation ", i, "...")
        n+=1
        while len(next_gen) < pop_size:
            # print("A")
            parents,parent_indices = ranked_selection(population_pool, 0.15) #need to save the parent indices
            # children = breed(parents) #children should both take the springs and masses of the smaller parent
            children = breed_v3(parents,parent_indices, pool_masses, pool_springs)
            children = [mutate_individual(mut_rate,c) for c in children]
            [next_gen.append(p) for p in parents]
            [next_gen.append(c) for c in children]


            next_masses.append(pool_masses[parent_indices[0]]) #first add parent masses
            next_masses.append(pool_masses[parent_indices[1]])
            

            next_springs.append(pool_springs[parent_indices[0]]) #then add parent springs
            next_springs.append(pool_springs[parent_indices[1]])

            # if len(parents[0]) >= len(parents[1]): #children inherit springs and masses of the smaller parent
            [next_masses.append(pool_masses[parent_indices[i]]) for i in range(2)]
            [next_springs.append(pool_springs[parent_indices[i]]) for i in range(2)]
            # else:
            #     [next_masses.append(pool_masses[parent_indices[0]]) for i in range(2)]
            #     [next_springs.append(pool_springs[parent_indices[0]]) for i in range(2)]


        print("Done making next generation.")
        population_pool = [np.copy(i) for i in next_gen]
        pool_masses = [np.copy(j) for j in next_masses]
        pool_springs = [np.copy(k) for k in next_springs]
        
        fits = [eval_springs(pool_masses[i],pool_springs[i],population_pool[i]) for i in range(len(population_pool))]
        arginds = np.argsort(fits)
        population_pool = [population_pool[i] for i in arginds] #gotta also reorder the springs and masses
        population_pool = list(reversed(population_pool))
        pool_masses = [pool_masses[i] for i in arginds]
        pool_masses = list(reversed(pool_masses))
        pool_springs = [pool_springs[i] for i in arginds]
        pool_springs = list(reversed(pool_springs))
        gen_best = max(fits)
        print("Longest distance in generation was ",gen_best)
        best_fits.append(gen_best)
        next_gen = []
        next_springs = []
        next_masses = []
        # if n%3 == 0:
        for idx in range(int(len(population_pool)/2),len(population_pool)):
            # print("ngen: ", len(next_gen))
            m,s,c = mutate_morphology(pool_masses[idx], pool_springs[idx], population_pool[idx])
            pool_masses[idx] = m
            pool_springs[idx] = s
            population_pool[idx] = c
        
    input("Render best solution?")
    eval_springs(pool_masses[0], pool_springs[0],population_pool[0], render=True) 
    
    return(best_fits, population_pool[0],pool_masses[0],pool_springs[0])
    










def breed_v3(parents,parent_indices, pool_masses, pool_springs):
    print("breed call\n\n")
    print("child1")
    p1,p2 = parents
    print("p1 size: ",len(p1))
    print("p2 size: ",len(p2))
    n1 = random.choice(range(1,len(p1)))
    A = p1[:n1]
    print("A: ", len(A))
    subset_max_size = len(p1)-len(A) if len(p1) - len(A) < len(p2) else len(p2)
    subset_size = 1 if subset_max_size == 1 else random.choice(range(1,subset_max_size))
    n2 = random.choice([i for i in range(0,len(p2)+1-subset_size)])
    B = p2[n2:n2+subset_size]
    print("B: ", len(B))
    C = p1[-(len(p1)-len(np.concatenate((A,B)))):] if len(np.concatenate((A,B))) < len(p1) else []
    print("C: ", len(C))
    child1 = np.concatenate((A,B,C)) if C != [] else np.concatenate((A,B))
    
    ######
    
    print("child2")
    
    p2,p1 = parents
    print("p1 size: ",len(p1))
    print("p2 size: ",len(p2))
    n1 = random.choice(range(1,len(p1)))
    A = p1[:n1]
    print("A: ", len(A))
    subset_max_size = len(p1)-len(A) if len(p1) - len(A) < len(p2) else len(p2)
    subset_size = 1 if subset_max_size == 1 else random.choice(range(1,subset_max_size))
    n2 = random.choice([i for i in range(0,len(p2)+1-subset_size)])
    B = p2[n2:n2+subset_size]
    print("B: ", len(B))
    C = p1[-(len(p1)-len(np.concatenate((A,B)))):] if len(np.concatenate((A,B))) < len(p1) else np.array([])

    print("C: ", len(C))
    child2 = np.concatenate((A,B,C)) if C != [] else np.concatenate((A,B))
    return(child1,child2)



def ranked_selection( population_pool,p_c):
    probabilities = np.array([((1-p_c)**((i+1)-1))*p_c for i in range(len(population_pool)-1)] + [(1-p_c)**(len(population_pool))])
    probabilities /= probabilities.sum()
    indices = list(range(len(population_pool)))
    indices = np.random.choice(indices,size=2, p=probabilities, replace=False)
    chosen_ones = [population_pool[c] for c in indices]
    return(chosen_ones,indices)


def append_point(point,masses,springs,spring_constants):
    mass = np.array([point,np.array([0.0,0.0,0.0]),np.array([0.0,0.0,0.0]),np.array([0.0,0.0,0.0]),point])
    masses = np.append(masses,mass).reshape(len(masses)+1,5,3)
    for mass_idx1 in range(len(masses)-1):
        m1_p = masses[mass_idx1][0] #get pos
        length = np.linalg.norm(m1_p-point)
        spring = np.array([[[mass_idx1, len(masses)-1, 0, 0],[length, 0,0,5000]]])
        springs = np.concatenate((springs,spring))
        spring_constants = np.concatenate((spring_constants, np.array([spawn_spring()])))
    return(masses, springs,spring_constants)


def fatten_cube(masses,springs,spring_constants):
    invalid_point = True
    while invalid_point:
        chosen_masses = np.array(random.choices(masses,k=3))
        # print(chosen_masses)
        # print(chosen_masses)
        ch_m_pos = chosen_masses[:,0,:] 
        v1 = ch_m_pos[0]-ch_m_pos[1]
        v2 = ch_m_pos[2]-ch_m_pos[1]
        normal_vect = np.cross(v1,v2)
        range_x = np.array([np.mean(ch_m_pos[:,0])-random.random(), np.mean(ch_m_pos[:,0])*1.8+random.random()])
        # print("xrange: ",range_x)
        
        range_y = np.array([np.mean(ch_m_pos[:,1])-random.random(), np.mean(ch_m_pos[:,1])*1.8+random.random()])
        range_z = np.array([np.mean(ch_m_pos[:,2])-random.random(), np.mean(ch_m_pos[:,2])*1.8+random.random()])
        # print("yrange: ",range_y)
        # print("zrange: ", range_z)
        point = np.array([ random.random() *(range_x[1] - range_x[0]) + range_x[0] , random.random() *(range_y[1] - range_y[0]) + range_y[0] , random.random() *(range_z[1] - range_z[0]) + range_z[0] ])
        if point[1] < 0:
            continue
        point = point + random.random()*normal_vect
        if point[1] < 0:
            continue
        invalid_point = False
        # print(point)
        masses2,springs2,spring_constants2 = append_point(point,masses,springs,spring_constants)
        
    return(masses2,springs2,spring_constants2)

def slim_cube(masses,springs,spring_constants):
    chosen_mass_idx = secrets.choice(range(len(masses)))
    masses2 = np.delete(masses,chosen_mass_idx,axis=0)
    springs_idxs = springs[:,0,0:2]
    springs_to_remove = np.argwhere(springs_idxs == float(chosen_mass_idx))[:,0]
    springs2 = np.delete(springs, springs_to_remove,axis=0)
    spring_constants2 = np.delete(spring_constants, springs_to_remove,axis=0)
    springs2[:,0,0:2] = np.where(springs2[:,0,0:2] > float(chosen_mass_idx),springs2[:,0,0:2] -1,springs2[:,0,0:2])
    return(masses2,springs2,spring_constants2)

def mutate_morphology(masses,springs,spring_constants):
    # operation = np.random.choice(["Fatten", "Slim"],p=[0.75,0.25])
    operation = "Fatten"
    # print(len(masses))
    # if len(masses) < 10 or operation == "Fatten":
    if operation == "Fatten":
        masses2,springs2,spring_constants2 = fatten_cube(masses,springs,spring_constants)
    # print(operation)
    # operation = "Fatten"
    # elif operation == "Fatten":
    #     masses2,springs2,spring_constants2 = fatten_cube(masses,springs,spring_constants)
    else:
        masses2,springs2,spring_constants2 = slim_cube(masses,springs,spring_constants) #this seems to work fine
    
    return(masses2,springs2,spring_constants2)












def spawn_individual(springs):
    individual = []
    num_springs = len(springs)
    individual = np.zeros(3*num_springs).reshape(num_springs,3)
    # material_dict = {1:np.array([0.0,0.0,1000.0]),2:np.array([0.0,0.0,20000.0]),3:np.array([0.25,0.0,5000.0]),4:np.array([0.25,np.pi,5000.0])}
    for s in range(num_springs):
            # random.random() *(upper - lower) + lower generates a random rational number in the range (lower,upper)
            b = random.random() *(1 - 0) + 0
            c = random.random() *(2*np.pi - 0) + 0
            k = random.random() *(10000 - 0) + 0
            # k = 1000.0
            # material = secrets.choice([1,2,3,4])
            # print(np.array([b,c,k]))
            # input("continue?\n")
            # individual[s] = np.copy(material_dict[material])
            individual[s] = np.array([b,c,k])
    return(individual)

def spawn_spring():
    # random.random() *(upper - lower) + lower generates a random rational number in the range (lower,upper)
    # material_dict = {1:np.array([0.0,0.0,1000.0]),2:np.array([0.0,0.0,20000.0]),3:np.array([0.25,0.0,5000.0]),4:np.array([0.25,np.pi,5000.0])}
    b = random.random() *(1 - 0) + 0
    c = random.random() *(2*np.pi - 0) + 0
    k = random.random() *(10000 - 0) + 0
    # k = 1000.0
    # material = secrets.choice([1,2,3,4])
    
    individual = np.array([b,c,k])
    # return(np.copy(material_dict[material]))
    return(individual)

def initialize_population(population_size,springs):
    pool = []
    for i in range(population_size):
        pool.append(spawn_individual(springs))
    return(pool)

def mutate_individual(mutation_rate, individual):
    
    if random.choices([True, False], weights=[mutation_rate, 1-mutation_rate], k=1)[0]:
        indiv = copy.deepcopy(individual)
        chosen_s_idx = secrets.choice(range(len(indiv)))
        newb = indiv[chosen_s_idx][0]+random.random() *(indiv[chosen_s_idx][0]*0.2 + indiv[chosen_s_idx][0]*0.2) - indiv[chosen_s_idx][0]*0.2
        newc = indiv[chosen_s_idx][1]+random.random() *(indiv[chosen_s_idx][1]*0.2 + indiv[chosen_s_idx][1]*0.2) - indiv[chosen_s_idx][1]*0.2
        newk = indiv[chosen_s_idx][2]+random.random() *(indiv[chosen_s_idx][2]*0.2 + indiv[chosen_s_idx][2]*0.2) - indiv[chosen_s_idx][2]*0.2
        indiv[chosen_s_idx] = (newb, newc, newk)
        return(indiv)
    else:
        return(individual)


    
    


            











if __name__ == "__main__":
    # run_simulation(10,0.0001,0.9,0.7,-2,debug_mode=True)
    

    best_fits,population_pool,pool_masses,pool_springs = evolve_robot(10)

    # with open('best_fits3.pkl', 'wb') as f:
    #     pickle.dump(best_fits, f)

    # with open('population_pool3.pkl', 'wb') as f:
    #     pickle.dump(population_pool, f)
    # with open('pool_masses3.pkl', 'wb') as f:
    #     pickle.dump(pool_masses, f)

    # with open('pool_springs3.pkl', 'wb') as f:
    #     pickle.dump(pool_springs, f)


    # open a file, where you stored the pickled data
    # file = open('res5/pool_masses5.pkl', 'rb')
    # # dump information to that file
    # masses = pickle.load(file)
    # # close the file
    # file.close()

    # file = open('res5/pool_springs5.pkl', 'rb')
    # # dump information to that file
    # springs = pickle.load(file)
    # # close the file
    # file.close()

    # file = open('res5/population_pool5.pkl', 'rb')
    # # dump information to that file
    # constants = pickle.load(file)
    # # close the file
    # file.close()


    # eval_springs(masses, springs, constants,render=True)
    # masses = initialize_masses()
    # springs = initialize_springs(masses)
    # # # print(springs)
    # # # masses,springs = slim_cube(masses,springs)
    # # # initialize_scene(masses,springs,0, breath=False)
    # # # masses2,springs2 = fatten_cube(masses,springs)
    # # # masses3,springs3 = fatten_cube(masses2,springs2)
    # # # masses4,springs4 = fatten_cube(masses3,springs3)

    # for i in range(18):
    #     masses,springs,constants = mutate_morphology(masses,springs,spawn_individual(springs))
    # # initialize_scene(masses,springs,0, breath=False)
    # eval_springs(masses, springs, constants,render=True)
    # print(mutate_morphology(masses,springs))



    # with open('best_indiv.pkl', 'wb') as f:
    #     pickle.dump(best_pal, f)

    # with open('all_fits.pkl', 'wb') as f:
    #     pickle.dump(best_fits, f)


    # print(best_pal, '\n')
    # print("======","\n")
    # print(best_fits)
    

    # profiler = cProfile.Profile()
    # profiler.enable()
    # evolve_robot2(1)
    # profiler.disable()
    # stats = pstats.Stats(profiler).sort_stats('tottime')
    # stats.dump_stats('export-data')
    # stats.print_stats()