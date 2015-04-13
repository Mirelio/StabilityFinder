import numpy as np
def distance(data):
   
    clusters_means = {}
    clusters_data = {}
    clusters_variance = {}
    cluster_counter = 0
    delta = 0.01
    line_counter = 0

    """
    This script goes through the file of the steady state values of A2 and B2. Makes the first line into a cluster.
    Then going through each line one at a time, if the new line belongs to an existing cluster (mean of clusters +- delta) then it adds to it (and recalculates the mean of the cluster) or if it doesnt, it creates a new cluster.
    Returns the number of clusters within the data set
    """

    def update_means(clusters_means, key, new_value):
        #Calculate the mean value of the cluster: (old mean + new value) /2
        new_x = (clusters_means[key][0] + new_value[0])/2
        new_y = (clusters_means[key][1] + new_value[1])/2
        clusters_means[key] = [new_x, new_y]
        return clusters_means

    def total_variance(data):

        var = 1/(np.var(data))
        return var

    #def reached_ss(set_ss):
    #    for i in set_ss:
    #        print i
    #    return i


    total_var = total_variance(data)
    #j = reached_ss(set_ss)
    #print '1/total_var received', total_var

    def cluster_variance(cluster):
        var = np.var(cluster)
        return var
    
    for i in data:
        line_counter += 1
    
        if line_counter == 1:
            #Make the first line a cluster automatically
            clusters_means['Cluster 1'] = i
            x = i[0]
            y = i[1]
            clusters_data['Cluster 1'] = [[x, y]]
            cluster_counter = 1
        
        elif line_counter > 1:
            currentDict = clusters_means.copy()
            #Make a copy or else you add to it and loop again over it, going on forever
            keys_m = currentDict.keys() 
            keys_m.sort()
            flag = 'false'
            reach_end_clust = 0

            for cluster in keys_m:
                #Loop over all cluster means trying to find a match
                if i[0] < currentDict[cluster][0] + delta and i[0] > currentDict[cluster][0] - delta and i[1] < currentDict[cluster][1] + delta and i[1] > currentDict[cluster][1] - delta:
                    #If it is within the bounds of any cluster (means +- delta)
                    flag = 'true'
                    clusters_means = update_means(clusters_means, cluster, i)
                    clusters_data[cluster].append(i)
                    #Recalculate the mean of the cluster with the added value
                
                elif i[0] > currentDict[cluster][0] + delta or i[0] < currentDict[cluster][0] - delta or i[1] > currentDict[cluster][1] + delta or i[1] < currentDict[cluster][1] - delta:
                    #If no match yet, add to the failure counter
                    reach_end_clust += 1

                if reach_end_clust == len(currentDict) and flag == 'false':
                    #If you reached the end and no match, make a new cluster
                    cluster_counter += 1
                    clusters_means['Cluster '+str(cluster_counter)] = i
                    x = i[0]
                    y = i[1]
                    clusters_data['Cluster '+str(cluster_counter)] = [[x, y]]
                    break

    keys_clust = clusters_data.keys()
    keys_clust.sort()
    for cluster in keys_clust:
        clusters_variance[cluster] = cluster_variance(clusters_data[cluster])

    val = clusters_variance.values()
    median_clust_var = np.median(val)

    return cluster_counter, clusters_means, total_var, median_clust_var


if __name__ == "__main__":
    data = [[0.0057716004963361683, 21.460106255342478], [21.446048422013305, 0.0057827426964791552], [21.417452842505117, 0.0058055462195353482], [21.465099516190882, 0.0057676593209811649], [21.50962756437988, 0.0057326964875122448], [21.483200724489294, 0.0057533920763004195], [21.528663866895251, 0.0057179418713070047], [21.547086091385093, 0.0057036130766015746], [21.51436851978476, 0.0057289977907766729], [21.523482554864824, 0.0057219088443705504], [0.0057897647237369135, 21.437227986850335], [0.0058397154585380162, 21.37502369846894], [21.380853053524781, 0.0058349995465730156], [21.444812510398449, 0.0057837252415432671], [21.436486232003197, 0.0057903428776207733], [21.485867030903282, 0.0057512973382726536], [21.484900613592298, 0.0057520577650063505], [21.488305467920679, 0.0057493824377162755], [21.503043518032737, 0.0057378377758528628], [21.493088346256979, 0.0057456321503482552], [0.0057919570329482591, 21.43446451264488], [0.0058338729646908519, 21.382246654498232], [0.0062526068476419791, 20.900358940434469], [21.343928852166403, 0.0058650313737890038], [21.39740814407158, 0.0058216371661119109], [21.435090989841534, 0.0057914600807917865], [21.442254566181564, 0.0057857747423090732], [21.455764934123987, 0.0057750370321041928], [21.446243994662861, 0.0057825879028425555], [21.459559948407541, 0.0057720337275630283], [0.0057402874607778934, 21.499913796745471], [0.0057712053755584391, 21.46060885983459], [0.0059255253225552534, 21.27071666893902], [20.845329676408323, 0.0063044205499938463], [21.191827375644074, 0.0059921900549169058], [21.345903455288578, 0.0058634168004281098], [21.304159868946996, 0.0058977333371413006], [21.414050154513763, 0.0058082724823207924], [21.423380173719522, 0.0058008051056120408], [21.442464299390537, 0.0057855925339894724], [0.0057290537347853155, 21.514361648111823], [0.0057554284697995273, 21.480612450377425], [0.0058457039567069531, 21.367648736843545], [0.0059497647319582689, 21.241828892496393], [20.901219511177064, 0.0062517924942158062], [21.12726062598178, 0.0060479202726607091], [21.29263710643998, 0.0059072777248167967], [21.257971181474993, 0.0059361929177325244], [21.354214439550002, 0.0058566282641982379], [21.396129820036563, 0.0058226678065411942], [0.005740437174989438, 21.499726399408381], [0.005779662560565722, 21.449930340591333], [0.0058367291068231308, 21.37871611240957], [0.0059373165153894939, 21.256633081619064], [0.006022211173406275, 21.156887880170903], [0.0066458272545190187, 20.504380219180934], [20.860291999912072, 0.00629025328939935], [21.257630508479718, 0.0059364757305881335], [21.270127212199242, 0.0059260188789565411], [21.318835545732458, 0.0058856256978760462], [0.0057271559097434657, 21.516734917834352], [0.0057543822981807784, 21.481941575603539], [0.0057946594855639291, 21.431081548993948], [0.0058712564741739814, 21.336320563700156], [0.0059930376021632269, 21.190838550645712], [0.0062041092065073123, 20.952721929075249], [0.009146363638154003, 18.71730125140067], [21.070408551737341, 0.0060978825851640819], [21.157591634326486, 0.0060216037611192028], [21.246540652419672, 0.0059457933270371244], [0.0057347310162313841, 21.50700111678518], [0.0057486787397681262, 21.48921161995025], [0.0058003461213168572, 21.423959769397541], [0.0058169125210765695, 21.40328786587774], [0.00585349768249114, 21.358062242557498], [0.005988008296783121, 21.196711571572354], [0.0061537834931199584, 21.007962010626756], [0.0064541125039345821, 20.691397555684528], [20.843969479681146, 0.0063057086257552707], [21.167482769112784, 0.006013071617757158], [0.0057186260343790509, 21.527701410514759], [0.0057668013181631029, 21.466179034160621], [0.0057904995045874527, 21.436289554242521], [0.0057953663338821291, 21.430185841651429], [0.0058630058173674577, 21.346404948692896], [0.0058921232316152383, 21.310951186258162], [0.0059494821095051921, 21.242166090272871], [0.0061818523339432063, 20.977034246255073], [20.850859432855923, 0.0062991694968000207], [21.027600907576609, 0.0061360940751372496], [0.0057087538533255912, 21.540444989984632], [0.0057489531394560528, 21.488851512476124], [0.0057595506560449202, 21.475371999246665], [0.0058088080607278806, 21.413379509066662], [0.0058348671730774583, 21.381011926728458], [0.005872977182131602, 21.334224679217808], [0.0059386394497976686, 21.255062023104333], [0.0060485003405687174, 21.126601382277538], [0.0062772321239839262, 20.87410029730172], [0.0082102925633306349, 19.28164789870285]]
    #data =[[1.0922713750843864, 0.36289517806840688], [4.4723826651382215, 0.052200236038760471], [3.8359363398468802, 0.07018620628788709], [4.4740419504886582, 0.052165291737026762], [5.7285390609390516, 0.027264154294037016], [4.3809390475636949, 0.054507167893720676], [4.4050335388992607, 0.053897204656997398], [3.6092546243608714, 0.077967195966834948], [5.3089840118840845, 0.034475857921783898], [5.3505058478848255, 0.033725476385929973], [0.065030863809427006, 4.0009424548355383], [0.27933758012636994, 1.3802333543534973], [1.1421104432231637, 0.34552611770199471], [1.646775099910794, 0.22744502870033076], [2.905252477305305, 0.10916866364344975], [2.1278633385600116, 0.16614681050071078], [3.5384658700241798, 0.080581060660982001], [3.2609677192353703, 0.091831801496249421], [2.9065959904475056, 0.10910122588184301], [3.7545771259147971, 0.072893800755267094], [0.09660165816730909, 3.1550877322265989], [0.24253947076037491, 1.5594276441982255], [0.76958820367821557, 0.52648151944141874], [1.058526135224015, 0.37554588013964113], [1.3379833920289861, 0.28941167302798543], [1.3438011948841444, 0.28798822378133937], [1.8240184766483203, 0.20117845826766168], [1.917061188684779, 0.1892971306277702], [2.2029888740377928, 0.15894666249702216], [2.3263642657758337, 0.14810557084878803], [0.026750101096112585, 5.7601852704809486], [0.14846793556011542, 2.3219787211500669], [0.30157954946393012, 1.2901939936411368], [0.90549455704788384, 0.44414249589669597], [0.7430912522826425, 0.54580177598129576], [0.98436549744557933, 0.40625396112451673], [1.2276169561388626, 0.31889963845075298], [1.4547725776539417, 0.26295691035715668], [1.5448874184787329, 0.24521545542392076], [1.6528666232997042, 0.22645310723831122], [0.061004384864908917, 4.1391832098648518], [0.1957770643411498, 1.8651934572780837], [0.33491885646450803, 1.1747576944936482], [0.43916275918663311, 0.91517027140101936], [0.68612686520523303, 0.59200549551033188], [0.82711750078488511, 0.48852917012808939], [1.0874298262589404, 0.36466479268041657], [1.3166122904381836, 0.29474808801465963], [1.1787278615967827, 0.33366941946939443], [1.344699966635003, 0.28777130564342535], [0.065055991235017568, 4.0003825767495718], [0.098923636375790533, 3.1060098969613272], [0.16636053374829765, 2.1257132385253699], [0.41456298644750694, 0.96597659249683787], [0.43734816400811083, 0.91874604498648504], [0.64705197866591957, 0.62802560978623279], [0.76913931446840222, 0.52679995853129169], [0.88200592108373654, 0.45666677492466023], [0.9969415756379435, 0.40074223681080706], [1.3061167892923757, 0.29743207516726816], [0.037300283549235098, 5.1580421674240977], [0.10983908073619385, 2.8930377938695138], [0.20897289130210076, 1.7676547520243691], [0.29362781527160869, 1.3210444889818131], [0.37791987816292733, 1.0524183568716421], [0.54489420436854341, 0.74429924261026148], [0.62959800741543648, 0.64543904563462451], [0.68935390895273674, 0.58920164409143982], [0.88874120936453205, 0.45301265712212679], [0.96336379263443428, 0.41576966409523747], [0.026410135521579961, 5.7828617325038882], [0.1051929134199142, 2.9802455690286367], [0.16286386282123572, 2.1615120360695301], [0.27788120458501131, 1.3865627330875077], [0.30130457596720261, 1.291242163236757], [0.4472901771035418, 0.89948486526866789], [0.52601957027686919, 0.77024666588542356], [0.65879171754754962, 0.61679263600971557], [0.83250302514398178, 0.4852295043433395], [0.8526557447885067, 0.47322626504358434], [0.047595208086478963, 4.6672151955815231], [0.12499459468510049, 2.639714281163227], [0.17401037615341566, 2.0513958687224911], [0.23772505599580138, 1.5863010535518309], [0.25987007265206846, 1.469710571223362], [0.4190149665537562, 0.95639589057914498], [0.49833101531073021, 0.81150777569011412], [0.56478725118811435, 0.71866255982941796], [0.69799963461190329, 0.58180301895424302], [0.74576149635378119, 0.54380066494675239], [0.022274253614582448, 6.0552834628782461], [0.097196924554534631, 3.1425936417396336], [0.16233220839447532, 2.1670753228676709], [0.20178851221485899, 1.8194991284600937], [0.27244550976309906, 1.4106755985823189], [0.33936608104969612, 1.1608621705271649], [0.42493331324822159, 0.94392704559363672], [0.45518951908043126, 0.8847209297230999], [0.54695545565329817, 0.74156794219669653], [0.63538643573202469, 0.63957163087654634]]
    distance(data)
