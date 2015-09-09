"""
adapted from https://datasciencelab.wordpress.com/2013/12/27/finding-the-k-in-k-means-clustering/
all reference to Tibshirani, R., Walther, G. and Hastie, T (2001)
Estimating the number of clusters in a data set via the gap statistic.
J.R. Statist Soc B, 63, 411-423
"""

import k_means_clustering
import numpy as np
import random


def Wk(clusters_centroids, clusters):
   #k is the number of clusters
   K = len(clusters_centroids)
   #for each cluster
   dk = []
   for i in range(K):
       #for each point in the cluster
       dk_pre = []
       for c in clusters['Cluster '+str(i+1)]:
           a = np.linalg.norm(np.asarray(clusters_centroids['Cluster '+str(i+1)])-np.asarray(c))
           dk_pre.append(a**2)
       dk.append(sum(dk_pre)*(2*len(c)))
   wk = sum(dk)/(2*len(c))
   return wk

def bounding_box(X):
    xmin, xmax = min(X,key=lambda a:a[0])[0], max(X, key=lambda a:a[0])[0]
    ymin, ymax = min(X,key=lambda a:a[1])[1], max(X, key=lambda a:a[1])[1]
    return (xmin, xmax), (ymin, ymax)

def gap_statistic(X, kmeans_cutoff):
    (xmin, xmax), (ymin, ymax) = bounding_box(X)
    # Dispersion for real distribution
    ks = [1, 2, 3, 4]
    data_centrs = []
    clusts = []
    median_cluster_variances = []
    total_variances = []
    Wks = np.zeros(len(ks))
    Wkbs = np.zeros(len(ks))
    sk = np.zeros(len(ks))
    for indk, k in enumerate(ks):
        tmp_Wks = []
        clusters_centroids_tmp = []
        clusters_tmp = []
        total_variance_tmp = []
        median_clust_var_tmp = []
        #Test each k 3 times and take the median
        Xcounter = 0
        while Xcounter < 3:
            try:
                clusters_centroids, clusters, total_variance, median_clust_var = k_means_clustering.kmeans(X, k, kmeans_cutoff)
                Xcounter += 1
            except: # catch all exceptions
                continue
            clusters_centroids_tmp.append(clusters_centroids)
            clusters_tmp.append(clusters)
            total_variance_tmp.append(total_variance)
            median_clust_var_tmp.append(median_clust_var)
            #calculate wk for eack k for the data
            tmp_Wks.append(np.log(Wk(clusters_centroids, clusters)))
        Wks[indk] = np.median(np.array(tmp_Wks))
        idx = tmp_Wks.index(Wks[indk])
        total_variances.append(total_variance_tmp[idx])
        median_cluster_variances.append(median_clust_var_tmp[idx])
        data_centrs.append(clusters_centroids_tmp[idx].values())
        clusts.append(clusters_tmp[idx].values())

        # Create B reference datasets
        B = 10
        Bcounter = 0
        BWkbs = np.zeros(B)
        for i in range(B):
            Xb = []
            for n in range(len(X)):
                Xb.append([random.uniform(xmin, xmax),
                          random.uniform(ymin, ymax)])
            Xb = np.array(Xb)
            while Bcounter < 10:
            	try:
                	clusters_centroids, clusters, total_variance, median_clust_var = k_means_clustering.kmeans(Xb, k, kmeans_cutoff)
                	Bcounter += 1
            	except:
                	continue
            BWkbs[i] = np.log(Wk(clusters_centroids, clusters))
        #Calculate Wk for each k in the reference data set
        Wkbs[indk] = sum(BWkbs)/B
        sk[indk] = np.sqrt(sum((BWkbs-Wkbs[indk])**2)/B)
    sk = sk*np.sqrt(1+1/B)
    return ks, Wks, Wkbs, sk, data_centrs, clusts, total_variances, median_cluster_variances

def distance(data, kmeans_cutoff):
    #Jitter is added to the data because when you have integers as data they overlap and the clusters fail.
    # if centres are chosen as points with the same coordinates, all the surrounding points will be assigned to only one of them and one centre will remain empty
    def rand_jitter(arr):
        stdev = .01*(max(arr)-min(arr))
        mu = np.mean(arr)
        if stdev == 0.0 and mu == 0.0:
            stdev = 0.000000001
        arr_j = []
        for j in arr:
            t = j + np.random.normal(mu, stdev)
            arr_j.append(t)
        return arr_j

    data_x, data_y = zip(*data)
    data_x_j = rand_jitter(data_x)
    data_y_j = rand_jitter(data_y)
    data = zip(data_x_j, data_y_j)

    ks, logWks, logWkbs, sk, clusters_means, clusts, total_variances, median_cluster_variances = gap_statistic(data, kmeans_cutoff)
    gaps = []
    for i in range(len(ks)):
        gaps.append(logWkbs[i]-logWks[i])
    #Find the smallest k such that Gap(k) > Gap(k+1) -  std_{k+1}
    cluster_counter = 0
    for i in range(len(gaps)):
        cluster_counter += 1
        #If you are at the last one and hasn't found one yet, there is no clustering
        if i == len(gaps)-1:
            cluster_counter = 1
            break
        if gaps[i] >= (gaps[i+1]-sk[i+1]):
            break
    return cluster_counter, clusters_means[cluster_counter-1], total_variances[cluster_counter-1],  median_cluster_variances[cluster_counter-1]

if __name__ == "__main__":
    #points=[]
    # create three random 2D gaussian clusters
    #for i in range(3):
    #    x=random.random()*3
    #    y=random.random()*3
    #    c=[scipy.array((x+random.normalvariate(0,0.1), y+random.normalvariate(0,0.1))) for j in range(100)]
    #    points+=c
    #import scipy
    #x=random.random()*3
    #y=random.random()*3
    #data=[scipy.array((x+random.normalvariate(0,0.1), y+random.normalvariate(0,0.1))) for j in range(100)]
    data = [[ 0.91834991,  1.30808191],[ 0.92816668,  1.26155501],[ 0.98862922,  1.06530509],[ 0.83100366,  0.95774705],[ 0.84137371,  1.07639981],[ 0.68551026,  1.2034627 ],[ 0.81750967,  1.2042546 ],[ 0.64188772,  1.16295477],[ 0.7928748 ,  1.02963283],[ 0.66370784,  1.18433277],[ 0.7306066 ,  1.08853561],[ 0.70332248,  1.03332626],[ 0.79875132,  1.17418049],[ 0.86567257,  1.25595848],[ 0.77612978,  1.34759302],[ 0.77651258,  0.99893465],[ 0.87541495,  1.04990709],[ 0.64625126,  1.04233455],[ 0.82469828,  1.19165142],[ 0.71429847,  1.10218565],[ 0.82028649,  1.07557068],[ 0.68273994,  1.26829369],[ 0.76646481,  1.15633825],[ 0.88886477,  1.21650525],[ 0.67260336,  1.14875754],[ 0.99912022,  1.04864659],[ 0.95759571,  1.0093166 ],[ 0.73968898,  1.14430582],[ 0.84997323,  1.22758536],[ 0.79549948,  1.32927399],[ 0.93231459,  1.03170249],[ 0.67674203,  1.19450648],[ 0.85346555,  1.22607725],[ 0.75697596,  0.97679794],[ 0.90742488,  1.15027835],[ 1.06819992,  1.14230133],[ 0.64627327,  1.02152947],[ 0.83353456,  1.15021777],[ 0.81954172,  1.04052559],[ 0.86337482,  1.21380789],[ 0.90654315,  1.03775222],[ 0.88939961,  1.29373957],[ 0.84944659,  1.23601006],[ 0.73264229,  0.99193911],[ 0.82246958,  1.16486363],[ 0.60009548,  1.17660045],[ 0.55934129,  1.06576623],[ 0.71980944,  1.11421697],[ 1.09468213,  1.21073363],[ 0.7318441 ,  1.18538137],[ 0.68994825,  1.08115755],[ 0.66114306,  1.07840125],[ 0.94038379,  1.09211519],[ 0.82848131,  1.33237235],[ 0.83800392,  1.22500974],[ 0.87869261,  1.15998055],[ 0.92304239,  1.30236263],[ 0.90894248,  1.19649736],[ 0.73113381,  1.11737312],[ 0.84423214,  1.12776486],[ 0.73550336,  1.04339863],[ 0.90193217,  1.2266133 ],[ 0.85819706,  1.12652772],[ 0.79507662,  1.3071297 ],[ 0.79472759,  1.23025154],[ 0.77286983,  1.2801619 ],[ 0.82911113,  1.13135955],[ 0.6917416 ,  1.22463456],[ 0.69892801,  1.26313425],[ 0.8635867 ,  1.16979022],[ 0.85124816,  1.05247787],[ 0.84975417,  1.17726869],[ 0.77588519,  1.19461212],[ 0.71534565,  1.23254908],[ 0.60752635,  1.15570501],[ 0.60868127,  1.27407933],[ 0.69201702,  1.08242579],[ 0.78021779,  0.94344003],[ 1.05084977,  1.24049917],[ 0.87415953,  1.25567937],[ 0.83054021,  0.97698555],[ 0.62781176,  1.07837645],[ 0.77179872,  1.29919688],[ 0.79382839,  1.10482194],[ 0.62210845,  1.14825983],[ 0.67377704,  1.35665964],[ 0.76816568,  1.29546742],[ 0.92939162,  1.17115994],[ 0.89176983,  1.22504591],[ 0.85223214,  1.16404655],[ 0.90225302,  1.10463866],[ 0.83039694,  1.23004263],[ 0.58738576,  1.2934131 ],[ 0.6530569 ,  1.11553704],[ 0.86024716,  1.31557616],[ 0.7737695 ,  0.89390437],[ 0.62893777,  1.01749657],[ 0.71407994,  1.03599486],[ 0.83612701,  1.28471681],[ 0.89055149,  1.07981299],[ 0.16995267,  1.57840243],[ 0.12387328,  1.49789509],[ 0.2736939 ,  1.60539245],[ 0.2240647 ,  1.42488629],[ 0.21292757,  1.62204674],[ 0.15324191,  1.4437909 ],[ 0.16985784,  1.56871821],[ 0.28998479,  1.53727789],[ 0.12662941,  1.44139047],[ 0.24431541,  1.57083197],[ 0.18643814,  1.61583563],[ 0.22822639,  1.50627176],[ 0.16888512,  1.43621669],[ 0.17158113,  1.54336183],[ 0.05571028,  1.48663104],[ 0.05470417,  1.38690772],[ 0.3136592 ,  1.41497982],[ 0.1967317,  1.5299   ],[ 0.31060869,  1.35881208],[ 0.35464153,  1.38295475],[ 0.24891971,  1.58277162],[ 0.15196336,  1.63676196],[ 0.15525866,  1.54230181],[ 0.15459121,  1.61066458],[ 0.05788808,  1.50059086],[ 0.26905819,  1.43168376],[ 0.26660292,  1.35822793],[ 0.24473189,  1.49600934],[ 0.18916845,  1.4387297 ],[ 0.38229891,  1.57043131],[ 0.3555571 ,  1.32679887],[ 0.30596285,  1.61424442],[ 0.36921116,  1.53078594],[ 0.06046067,  1.36489181],[ 0.18887229,  1.48427352],[ 0.25623035,  1.45806074],[ 0.12593923,  1.33918034],[ 0.16445422,  1.55510623],[ 0.12525853,  1.42285783],[ 0.06562813,  1.33905937],[ 0.23757609,  1.60797719],[ 0.22313972,  1.55338975],[ 0.147428  ,  1.37397787],[ 0.0341722 ,  1.41688207],[ 0.31165022,  1.58589016],[ 0.20006498,  1.46316724],[ 0.13810251,  1.40866614],[ 0.19101441,  1.51640411],[ 0.16347579,  1.3795385 ],[ 0.18059221,  1.55781839],[ 0.25568423,  1.60080664],[ 0.07970394,  1.52667819],[ 0.13425731,  1.61270168],[ 0.37606837,  1.6615328 ],[ 0.31619603,  1.34938993],[ 0.09927083,  1.45174274],[ 0.25375533,  1.58546261],[ 0.14278615,  1.64274881],[ 0.44485414,  1.64257425],[ 0.21622064,  1.57550861],[ 0.24292632,  1.31017755],[ 0.11043325,  1.55399189],[ 0.22782675,  1.47487885],[ 0.08595696,  1.502926  ],[ 0.20713081,  1.48674897],[ 0.01161609,  1.75664577],[ 0.1948073 ,  1.46347762],[ 0.00568651,  1.42153312],[ 0.18688127,  1.54994092],[ 0.08508039,  1.5025292 ],[ 0.16532625,  1.58822454],[ 0.20497902,  1.66399917],[ 0.31175383,  1.50644542],[ 0.29881545,  1.65813922],[-0.10000791,  1.60552253],[ 0.02449594,  1.57081881],[ 0.05873665,  1.50312296],[ 0.13313773,  1.56066257],[ 0.1150732 ,  1.46110076],[ 0.20003581,  1.48835331],[ 0.22626407,  1.60625565],[ 0.21536726,  1.42786334],[ 0.11341284,  1.59804981],[ 0.11433275,  1.52577339],[ 0.26536766,  1.53634784],[ 0.1638084 ,  1.54827785],[ 0.14358996,  1.46389633],[ 0.29145412,  1.32912338],[ 0.31149263,  1.59463776],[ 0.28939476,  1.53287588],[ 0.19592242,  1.50168978],[ 0.0992257 ,  1.29647896],[ 0.27434447,  1.40504847],[ 0.2614714 ,  1.56794976],[ 0.14745487,  1.59143531],[ 0.1238065 ,  1.34600576],[ 0.44533393,  1.59067446],[ 0.17610852,  1.4959937 ],[ 0.20090959,  1.35558533],[ 0.13481942,  1.70090286],[ 1.795734  ,  1.48006454],[ 1.72051479,  1.43460186],[ 1.79171411,  1.55983252],[ 1.71290682,  1.57670209],[ 1.89836721,  1.67378668],[ 1.69131609,  1.47010715],[ 1.55108442,  1.58293425],[ 1.68685952,  1.61192571],[ 1.78132461,  1.47774602],[ 1.71168629,  1.48548465],[ 1.87048623,  1.45027215],[ 1.75879078,  1.44228332],[ 1.76220331,  1.40977643],[ 1.68163328,  1.49760796],[ 1.76461937,  1.81028796],[ 1.84805776,  1.71801683],[ 1.70600838,  1.53962549],[ 1.53544814,  1.46830936],[ 1.93198557,  1.58238697],[ 1.80946756,  1.42309513],[ 1.71791654,  1.48018185],[ 1.64777995,  1.39851881],[ 1.70658457,  1.4804636 ],[ 1.80328148,  1.44064482],[ 1.71772424,  1.45202207],[ 1.70450494,  1.67175771],[ 1.66135491,  1.4273386 ],[ 1.99172448,  1.51004969],[ 1.49021739,  1.73279208],[ 1.62696495,  1.35532825],[ 1.51973195,  1.51968004],[ 1.66249353,  1.52267635],[ 1.7673944,  1.6506378],[ 1.68507215,  1.63487169],[ 1.84374412,  1.72273016],[ 1.51330004,  1.57539713],[ 1.72692696,  1.77435763],[ 1.71165096,  1.55542996],[ 1.51465408,  1.52094299],[ 1.55657982,  1.52216475],[ 1.86570583,  1.56685378],[ 1.48598407,  1.67246859],[ 1.63577634,  1.64171715],[ 1.63673733,  1.59291091],[ 1.50850008,  1.37012063],[ 1.55480649,  1.61646538],[ 1.54650838,  1.48483709],[ 1.66201567,  1.53391701],[ 1.71618288,  1.42158355],[ 1.88019792,  1.60435637],[ 1.78146104,  1.74043354],[ 1.78033194,  1.7089019 ],[ 1.7973951 ,  1.67295621],[ 1.65918848,  1.56761507],[ 1.68220314,  1.57271606],[ 1.66990092,  1.64646914],[ 1.66616281,  1.52181827],[ 1.84203123,  1.55693265],[ 1.51898726,  1.53739076],[ 1.63494006,  1.61807206],[ 1.80438332,  1.51565881],[ 1.76202774,  1.76018886],[ 1.4890676 ,  1.63146733],[ 1.72310866,  1.49704862],[ 1.64517664,  1.43268949],[ 1.7885635 ,  1.53237552],[ 1.81648151,  1.7384386 ],[ 1.64863285,  1.61115335],[ 1.71538459,  1.50463321],[ 1.68337293,  1.63422617],[ 1.81424583,  1.38623915],[ 1.72094196,  1.55683112],[ 1.68555748,  1.52254208],[ 1.60868903,  1.39634783],[ 1.72610009,  1.54239749],[ 1.6694734 ,  1.71636083],[ 1.77508834,  1.65200479],[ 1.68646625,  1.69431401],[ 1.69455411,  1.38609659],[ 1.6432618,  1.6081985],[ 1.96182352,  1.63426194],[ 1.56943622,  1.56944866],[ 1.71290916,  1.51356301],[ 1.4719348 ,  1.40659353],[ 1.66807672,  1.52116187],[ 1.66581434,  1.5571652 ],[ 1.83864643,  1.48807522],[ 1.58923291,  1.37161432],[ 1.74333296,  1.50451419],[ 1.63190061,  1.71631183],[ 1.677219 ,  1.4775572],[ 1.473265  ,  1.54090041],[ 1.61378767,  1.68105113],[ 1.84977761,  1.71713531],[ 1.5910113 ,  1.58654803],[ 1.58021214,  1.5301999 ],[ 1.69160347,  1.55470384],[ 1.71929249,  1.57434886],[ 1.50232926,  1.5841234 ],[ 1.98520492,  1.4366421 ]]
    distance(data, 0.00001)

    #x, y = zip(*data)
    #plt.scatter(x, y)
    #plt.show()
