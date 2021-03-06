import read_input
import numpy
from numpy import random
import copy
import time
import operator
import sampl_initi_condit
import deterministic_clustering
import gap_statistic
import logging
import steady_state_check
import math
import os
import cudasim
import cudasim.Lsoda as Lsoda
import cudasim.EulerMaruyama as EulerMaruyama
import cudasim.Gillespie as Gillespie
import sys, getopt


def central():
    start = time.time()
    opts, args = getopt.getopt(sys.argv[1:], "hi:o:l:", ["ifile=", "ofile=", "lfile="])
    for opt, arg in opts:
        if opt in ("-l", "--lfile"):
            logging.basicConfig(filename=arg, level=logging.INFO)

        if opt in ("-i", "--ifile"):
            epsilons_final, final_desired_values, ss_std, cluster_mean_min, number_particles,\
           number_to_sample, init_cond_to_sample, alpha, st, end, twidth, species_numb_to_fit, stoch_determ, \
           clustering, model_file, sbml_name, lims, ics, dt, det_clust_delta, kmeans_cutoff, cell_volume_first_param = read_input.inp(arg)

        if opt in ("-o", "--ofile"):
            if not os.path.exists(arg):
                os.makedirs(arg)
                results_path = arg

    logger.info('==============================================')
    logger.info('INPUTS')
    logger.info('epsilons: %s', epsilons_final)
    logger.info('particles: %s', number_particles)
    logger.info('model name: %s', model_file)
    logger.info('species to fit: %s', species_numb_to_fit)
    logger.info('integration: %s', stoch_determ)
    logger.info('clustering: %s', clustering)
    logger.info('priors: %s', lims)
    logger.info('initial conditions: %s', ics)
    logger.info('results folder: %s', results_path)
    logger.info('First parameter ignored: %s', cell_volume_first_param)
    alpha = math.ceil(alpha*number_particles)
    pop_indic = 0
    finishTotal = False

    times = numpy.arange(st, end, twidth)

    if model_file == 'sbml':
        write_cuda(stoch_determ, sbml_name)
    cudaCode = sbml_name+'.cu'
    if stoch_determ == 'ODE':
        import cudasim.Lsoda as Lsoda
        modelInstance = Lsoda.Lsoda(times, cudaCode, dt=dt)
    elif stoch_determ == 'SDE':
        import cudasim.EulerMaruyama as EulerMaruyama
        modelInstance = EulerMaruyama.EulerMaruyama(times, cudaCode, dt=dt)
    elif stoch_determ == 'Gillespie':
        import cudasim.Gillespie as Gillespie
        modelInstance = Gillespie.Gillespie(times, cudaCode, dt=dt)

    if pop_indic == 0:
        logger.info('==============================================')
        logger.info('RUN')
        logger.info('population: %s', pop_indic+1)
        parameters_sampled = sample_priors(number_to_sample, lims)
        cudasim_result = simulate_dataset(parameters_sampled, number_to_sample, init_cond_to_sample, stoch_determ, modelInstance, ics, lims)
        distances_matrix, set_results = measure_distance(cudasim_result, number_to_sample, final_desired_values, init_cond_to_sample, species_numb_to_fit, stoch_determ, det_clust_delta, kmeans_cutoff, clustering)
        parameters_accepted = parameters_sampled[0:int(number_particles)]
        accepted_distances = distances_matrix[0:int(number_particles)]
        simulations_accepted = set_results[0:int(number_particles)]
        #species_1_timec = species_1_timecourse[0:int(number_particles)]
        #species_2_timec = species_2_timecourse[0:int(number_particles)]
        pop_fold_res_path = 'Population_'+str(pop_indic+1)
        os.makedirs(results_path+'/'+pop_fold_res_path)
        current_weights_list = particle_weights(parameters_accepted)
        save_results_files(simulations_accepted, results_path, pop_fold_res_path, parameters_accepted, current_weights_list, pop_indic)
        pop_indic += 1

    while finishTotal == False:
        finished = False
        logger.info('==============================================')
        logger.info('population: %s', pop_indic+1)
        pop_fold_res_path = 'Population_'+str(pop_indic+1)
        os.makedirs(results_path+'/'+pop_fold_res_path)
        previous_parameters, previous_weights_list, epsilons = prepare_next_pop(parameters_accepted, current_weights_list, alpha, accepted_distances)

        parameters_accepted = []
        accepted_distances = []
        simulations_accepted = []
        #species_1_timec_acc = []
        #species_2_timec_acc = []
        while finished == False:

            parameters_sampled, current_sampled_weights = sample_params(previous_parameters, previous_weights_list, number_to_sample)
            perturbed_particles = perturb_particles(parameters_sampled, lims, cell_volume_first_param)
            cudasim_result = simulate_dataset(perturbed_particles, number_to_sample, init_cond_to_sample,stoch_determ, modelInstance, ics, lims)
            distances_matrix, set_results = measure_distance(cudasim_result, number_to_sample, final_desired_values, init_cond_to_sample, species_numb_to_fit, stoch_determ, det_clust_delta, kmeans_cutoff, clustering)
            parameters_sampled, distances_matrix, set_results = accept_reject_params(distances_matrix, perturbed_particles, epsilons, ss_std, cluster_mean_min, set_results, init_cond_to_sample)
            # Append the accepted ones to a matrix which will be built up until you reach the number of particles you want
            for i in parameters_sampled:
                parameters_accepted.append(i)
            for i in distances_matrix:
                accepted_distances.append(i)
            for i in set_results:
                simulations_accepted.append(i)
            #for i in species_1_timecourse:
            #    species_1_timec_acc.append(i)
            #for i in species_2_timecourse:
            #    species_2_timec_acc.append(i)

            if len(parameters_accepted) >= number_particles:
                parameters_accepted = parameters_accepted[0:int(number_particles)]
                accepted_distances = accepted_distances[0:int(number_particles)]
                simulations_accepted = simulations_accepted[0:int(number_particles)]
                finished = True
                logger.info('Reached number of particles')
            elif len(parameters_accepted) < float(number_particles):
                finished = False
                logger.info('Not reached number of particles, sampling again')
                logger.info('number of particles accepted: %s', len(parameters_accepted))
            if finished == True:
                break
        current_weights_list = perturbed_particle_weights(parameters_accepted, previous_parameters, lims)
        save_results_files(simulations_accepted, results_path, pop_fold_res_path, parameters_accepted, current_weights_list, pop_indic)
        pop_indic += 1
              
        if epsilons[0] <= epsilons_final[0] and epsilons[1] <= epsilons_final[1] and epsilons[2] <= epsilons_final[2]:
            finishTotal = True
            logger.info('Last population finished')
            final_weights = current_weights_list[:]
            final_particles = parameters_accepted[:][:]
            logger.info('Re-sampling posterior')
            #Sample from posterior
            post_samp, post_weights = sample_params(final_particles, final_weights, number_to_sample)
            cudasim_result = simulate_dataset(post_samp, number_to_sample, init_cond_to_sample, stoch_determ, modelInstance, ics, lims)
            distances_matrix, set_results = measure_distance(cudasim_result, number_to_sample, final_desired_values, init_cond_to_sample, species_numb_to_fit, stoch_determ, det_clust_delta, kmeans_cutoff, clustering)
            pop_fold_res_path = '/re_sampled_posterior'
            os.makedirs(results_path+'/re_sampled_posterior')
            for i in range(0, len(set_results)):
                numpy.savetxt(str(results_path)+'/re_sampled_posterior'+'/set_result'+str(i)+'.txt', set_results[i], delimiter=' ')
            end = time.time()
            logger.info('TIME: %s', end - start)
    return final_weights, final_particles, pop_fold_res_path, results_path, times


def prepare_next_pop(parameters_accepted, current_weights_list, alpha, distances_matrix):
    distances_matrix.sort(key=operator.itemgetter(0, 1, 2))
    epsilon_cl_current = distances_matrix[int(alpha)][0]
    epsilon_t_current = distances_matrix[int(alpha)][1]
    epsilon_vcl_current = distances_matrix[int(alpha)][2]
    epsilons = [epsilon_cl_current, epsilon_t_current, epsilon_vcl_current]
    logger.info('epsilons: %s', epsilons)
    return parameters_accepted, current_weights_list, epsilons


def sample_priors(number_to_sample, lims):
    logger.info('sampling priors')
    parameters_list = []
    partic_indic = 0
    while partic_indic <= number_to_sample:
        params = []
        for i in lims:
                if i[0] == 'constant':
                    params.append(float(i[1]))
                if i[0] == 'uniform' or i[0] == 'log':
                    params.append(random.uniform(low=i[1], high=i[2]))
                #if i[0] == 'lognormal':
                #    params.append(random.lognormal(mean=i[1], sigma=i[2]))
        parameters_list.append(params)
        partic_indic += 1
        if partic_indic == number_to_sample:
            break
    return parameters_list


def sample_params(parameters_accepted, current_weights_list, number_to_sample):

    def choose_sample(current_weights_list):
        #Bernouli trials
        #Choose a random number between 0 and 1
        n = random.random_sample()
        for i in range(0, len(current_weights_list)):
            #|-----|--|-------|---|-----|
            #If you are in the current segment, great!
            if n < current_weights_list[i]:
                break
            #if not, go to the next segment and remove the - you already counted
            n = n - current_weights_list[i]
            #Great, you've got your -!
        return i
       
    weights_val_list = []
    partic_indic = 0
    weight_index_list = []
    parameters_list = []
    while partic_indic < number_to_sample:
        sample = choose_sample(current_weights_list)
        weight_index_list.append(sample)
        partic_indic += 1
        if partic_indic == number_to_sample:
            break
    for index in weight_index_list:
        weight_val = current_weights_list[index]
        weights_val_list.append(weight_val)
        param = parameters_accepted[index]
        parameters_list.append(param)
    return parameters_list, weights_val_list

def write_cuda(stoch_determ, sbml_name):
    import cudasim.SBMLParser as Parser
    #Location of SBML model file
    xmlModel = sbml_name+'.xml'
    name = sbml_name
    # create CUDA code from SBML model
    if stoch_determ == 'ODE':
        Parser.importSBMLCUDA([xmlModel], ['ODE'], ModelName=[name])
    elif stoch_determ == 'Gillespie':
        Parser.importSBMLCUDA([xmlModel], ['MJP'], ModelName=[name])
    return


def simulate_dataset(parameters_sampled, number_to_sample, init_cond_to_sample, stoch_determ, modelInstance, ics, lims):
    logger.info('Simulating...')

    #If one of the parameteres is log distribution, give the simulator 10^x rather than x.
    altered_param_list = []
    for p in parameters_sampled:
        p_count = -1
        alt_tmp = []
        for i in p:
            p_count += 1
            if lims[p_count][0] == 'log':
                alt_tmp.append(10**i)
            else:
                alt_tmp.append(i)
        altered_param_list.append(alt_tmp)
    expanded_params_list = []
    for i in altered_param_list:
        for j in range(0, init_cond_to_sample):
            expanded_params_list.append(i)
    init_cond_list = sampl_initi_condit.sample_init(number_to_sample, init_cond_to_sample, ics)
    result = modelInstance.run(expanded_params_list, init_cond_list)
    return result

def measure_distance(cudasim_result, number_to_sample, final_desired_values, init_cond_to_sample, species_numb_to_fit, stoch_determ, det_clust_delta, kmeans_cutoff, clustering):
    set_results = []
    #species_1_timecourse = []
    #species_2_timecourse = []
    logger.info('Measuring distance...')
    distances_matrix = []
    meas_dis = []
    def rand_jitter(arr):
        stdev = .01*(max(arr)-min(arr))
        mu = numpy.mean(arr)
        arr_j = []
        for j in arr:
            t = j + numpy.random.normal(mu, stdev)
            arr_j.append(t)
        return arr_j

    for i in range(0, int(number_to_sample)):
        range_start = i*int(init_cond_to_sample)
        range_end = i*int(init_cond_to_sample) + int(init_cond_to_sample) - 1
        #[#threads][#beta][#timepoints][#speciesNumber]
        set_result1 = cudasim_result[range_start:range_end, 0, -1, int(species_numb_to_fit[0])-1]
        set_result2 = cudasim_result[range_start:range_end, 0, -1, int(species_numb_to_fit[1])-1]
        #set_result1_j = rand_jitter(set_result1)
        #set_result2_j = rand_jitter(set_result2)
        set_result = zip(set_result1, set_result2)
        set_results.append(set_result)
        ss_res_set1 = cudasim_result[range_start:range_end, 0, -10:, int(species_numb_to_fit[0])-1]
        ss_res_set2 = cudasim_result[range_start:range_end, 0, -10:, int(species_numb_to_fit[1])-1]

        #species_1_timecourse.append(cudasim_result[range_start:range_end, 0, :, int(species_numb_to_fit[0])-1])
        #species_2_timecourse.append(cudasim_result[range_start:range_end, 0, :, int(species_numb_to_fit[1])-1])

        ss_res_set = []
        for j in range(len(ss_res_set1)):
            ss_res_set.append(zip(ss_res_set1[j], ss_res_set2[j]))
        std_devs = steady_state_check.ss_check(ss_res_set)

        if clustering == 'det':
            cluster_counter, clusters_means, total_variance, median_clust_var = deterministic_clustering.distance(set_result, det_clust_delta)
            meas_dis.append([cluster_counter, total_variance, median_clust_var, std_devs[0], std_devs[1], clusters_means.values()])
            distances_matrix.append([abs(cluster_counter - final_desired_values[0]), abs(total_variance - final_desired_values[1]), abs(median_clust_var - final_desired_values[2]), std_devs[0], std_devs[1], clusters_means.values()])
        elif clustering == 'gapstatistic':
            cluster_counter, clusters_means, total_variance, median_clust_var = gap_statistic.distance(set_result, kmeans_cutoff)
            meas_dis.append([cluster_counter, total_variance, median_clust_var, std_devs[0], std_devs[1], clusters_means])
            distances_matrix.append([abs(cluster_counter - final_desired_values[0]), abs(total_variance - final_desired_values[1]), abs(median_clust_var - final_desired_values[2]), std_devs[0], std_devs[1], clusters_means])
    xyz = zip(*meas_dis)
    logger.info('----------Distances---------- ')
    logger.info('number of clusters min/max: %s', [min(xyz[0]), max(xyz[0])])
    logger.info('total variance min/max: %s', [min(xyz[1]), max(xyz[1])])
    logger.info('cluster variance min/max: %s', [min(xyz[2]), max(xyz[2])])
    logger.info('steady state standard deviation min/max, species1: %s', [min(xyz[3]), max(xyz[3])])
    logger.info('steady state standard deviation min/max, species2: %s', [min(xyz[4]), max(xyz[4])])
    logger.info('cluster mean level min/max: %s', [(min(a), max(a)) for a in zip(*xyz[5])])

    return distances_matrix, set_results

def accept_reject_params(distances_matrix, parameters_sampled, epsilons, ss_std, cluster_mean_min, set_results, init_cond_to_sample):
    passed_simulations = []
    #Reject the paramss>e.
    fail_counter_0 = 0
    fail_counter_1 = 0
    fail_counter_2 = 0
    fail_counter_3 = 0
    fail_counter_4 = 0
    fail_counter_5 = 0
    index_to_delete = []
    totlist = len(distances_matrix)
    for index, item in enumerate(distances_matrix):
        #epsilon_cl_current is the distance of current alpha to desired behaviour
        #item!=item is a check in case the value is nan
        if item[0] > epsilons[0] or item[0] != item[0]:
            index_to_delete.append(index)
            fail_counter_0 += 1

        if item[1] > epsilons[1] or item[1] != item[1]:
            index_to_delete.append(index)
            fail_counter_1 += 1

        if item[2] > epsilons[2] or item[2] != item[2]:
            index_to_delete.append(index)
            fail_counter_2 += 1

        if item[3] > ss_std or item[4] > ss_std:
            index_to_delete.append(index)
            fail_counter_3 += 1

        if len(item[5]) >= 2:
            counter = 0
            for it in item[5]:
                if it[0] > cluster_mean_min or it[1] > cluster_mean_min:
                    counter += 1
            if counter < 2:
                index_to_delete.append(index)
                fail_counter_4 += 1

        # if len(item[5]) == 3:
        #     counter = 0
        #     for it in item[5]:
        #         if it[0] < cluster_mean_min or it[1] < cluster_mean_min:
        #             counter += 1
        #     if counter != 0:
        #         index_to_delete.append(index)
        #         fail_counter_5 += 1
    #get the unique values by converting the list to a set
    index_to_delete = set(index_to_delete)
    index_to_delete_l = list(index_to_delete)
    sorted_index_delete = sorted(index_to_delete_l)
    if len(sorted_index_delete) > 0:
        for index in reversed(sorted_index_delete):
            del distances_matrix[index]
            del parameters_sampled[index]
            del set_results[index]
            #del species_1_timecourse[index]
            #del species_2_timecourse[index]

    logger.info('----------Fails----------')
    logger.info('number of clusters: %s', fail_counter_0)
    logger.info('total variance: %s', fail_counter_1)
    logger.info('cluster variance: %s', fail_counter_2)
    logger.info('steady state standard deviation: %s', fail_counter_3)
    logger.info('steady state level: %s', fail_counter_4)
    logger.info('third steady state level: %s', fail_counter_5)
    return parameters_sampled, distances_matrix, set_results

def save_results_files(simulations_accepted, results_path, pop_fold_res_path, parameters_accepted, current_weights_list, pop_indic ):
    numpy.savetxt(results_path+'/'+str(pop_fold_res_path)+'/data_Population'+str(pop_indic+1)+'.txt', parameters_accepted, delimiter=' ')
    numpy.savetxt(results_path+'/'+str(pop_fold_res_path)+'/data_Weights'+str(pop_indic+1)+'.txt', current_weights_list, delimiter=' ')
    for i in range(0, len(simulations_accepted)):
        numpy.savetxt(str(results_path)+'/'+str(pop_fold_res_path)+'/set_result'+str(i)+'.txt', simulations_accepted[i], delimiter=' ')
    return


def particle_weights(parameters_sampled):
    logger.info('Calculating weights')
    weights_list = []
    #Weights of particles for t=0
    for i in range(len(parameters_sampled)):
        weights_list.append(1)

    #Normalise the weights
    n = sum(weights_list)
    for i in range(len(weights_list)):
        weights_list[i] = float(weights_list[i])/float(n)

    return weights_list


def perturb_particles(parameters_sampled, lims, cell_volume_first_param):
    logger.info('Perturbing particles')
    ##Make a new list which will be used so that you don't confuse them with the sampled parameters
    not_perturbed_particles = copy.deepcopy(parameters_sampled)
    perturbed_particles = []
    for particle in not_perturbed_particles:
        part_params = []
        for i in range(0, len(particle)):
            if cell_volume_first_param == 'True' and i == 0:
                part_params.append(1.0)
            else:
                minimum = min(param[i] for param in parameters_sampled)
                maximum = max(param[i] for param in parameters_sampled)
                scale = (maximum-minimum)/2

                if particle[i] + scale < float(lims[i][2]) and particle[i] - scale > float(lims[i][1]):
                    delta_perturb = random.uniform(low=-scale, high=scale)
                    part_params.append(particle[i] + delta_perturb)
                    i += 1
                elif particle[i] + scale > float(lims[i][2]):
                    delta_perturb = random.uniform(low=-scale, high= float(lims[i][2])-particle[i])
                    part_params.append(particle[i] + delta_perturb)
                    i += 1
                elif particle[i] - scale < float(lims[i][1]):
                    delta_perturb = random.uniform(low=float(lims[i][1])-particle[i], high=scale)
                    part_params.append(particle[i] + delta_perturb)
                    i += 1
            if i == len(particle):
                perturbed_particles.append(part_params)
    return perturbed_particles


def uniform_pdf(x, a, b):
    j = 0
    if x <= b and x > a:
        j = b-a
        return 1/j
    else:
        return 0


def perturbed_particle_weights(parameters_accepted, previous_parameters, lims):
    logger.info('Calculating weights')
    current_weights_list = []
    #numerator
    num_tmp = []
    for i in range(1, len(lims)):
        minimum_pert = float(lims[i][1])
        maximum_pert = float(lims[i][2])
        numer = 1/(maximum_pert-minimum_pert)
        num_tmp.append(numer)
    numerator = reduce(operator.mul, num_tmp, 1)
    #denominator
    for particle in range(len(parameters_accepted)):
        #Calculate the probability for each parameter of the particle
        params_denom = []
        for paramet in range(1, len(lims)):
            denominator_tmp = []
            minimum_prev = min(param[paramet] for param in previous_parameters)
            maximum_prev = max(param[paramet] for param in previous_parameters)
            delta = (maximum_prev-minimum_prev)/2
            for prev_particle in range(len(previous_parameters)):
                denominator_tmp.append(uniform_pdf(parameters_accepted[particle][paramet], previous_parameters[prev_particle][paramet]-delta, previous_parameters[prev_particle][paramet]+delta))
            params_denom.append(sum(denominator_tmp))

        #reduce calculates the cumulative sum from left to to right.
        #operator.mul multiplies
        #this is equivalent to for i in list, p*=i
        particle_denominator = reduce(operator.mul, params_denom, 1)
        current_weights_list.append(numerator/particle_denominator)
              
    #Normalise the weights
    n = sum(current_weights_list)
    for i in range(len(current_weights_list)):
        current_weights_list[i] = float(current_weights_list[i])/float(n)
    return current_weights_list

logger = logging.getLogger(__name__)
final_weights, final_particles, pop_fold_res_path, results_path, times = central()
final_path_v = str(results_path)+'/Parameter_values_final.txt'
final_path_w = str(results_path)+'/Parameter_weights_final.txt'
numpy.savetxt(final_path_v, final_particles, delimiter=' ')
numpy.savetxt(final_path_w, final_weights, delimiter=' ')

#f1 = open('species_timecourse_1.txt', 'a')
#f2 = open('species_timecourse_2.txt', 'a')

#f_handle1 = file('species_timecourse_1.txt', 'a')
#f_handle2 = file('species_timecourse_2.txt', 'a')

#print times
#for i in range(0, len(species_1_timec)):
#        numpy.savetxt(f_handle1, species_1_timec[i])
#        numpy.savetxt(f_handle2, species_2_timec[i])
#f_handle1.close()
#f_handle2.close()
