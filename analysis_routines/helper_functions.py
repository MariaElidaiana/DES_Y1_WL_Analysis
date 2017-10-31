"""
This file contains functions used to make the analysis script easier to read. This includes file IO and loading various things.
"""
import numpy as np
from scipy.interpolate import interp2d

fullbase = "/home/tmcclintock/Desktop/des_wl_work"
#Y1 paths
y1base = fullbase+"/DATA_FILES/y1_data_files/"
y1base2 = y1base+"FINAL_FILES/"
y1database     = y1base2+"full-unblind-mcal-zmix_y1subtr_l%d_z%d_profile.dat"
y1JKcovbase      = y1base2+"full-unblind-mcal-zmix_y1subtr_l%d_z%d_dst_cov.dat"
y1SACcovbase     = y1base2+"NOT IMPLEMENTED YET"
y1boostbase    = y1base+"FINAL_FILES/full-mcal-zmix_y1clust_l%d_z%d_zpdf_boost.dat"
y1boostcovbase = y1base+"FINAL_FILES/full-mcal-zmix_y1clust_l%d_z%d_zpdf_boost_cov.dat"
#y1boostbase = y1base+"boost_files/redcurves/red_z%d_l%d.txt"
#y1boostcovbase = y1base+"boost_files/redcurves/cov_z%d_l%d.txt"

y1zspath   = y1base+"Y1_meanz.txt"
y1lamspath = y1base+"Y1_meanl.txt"
#SV paths
svbase = fullbase+"/DATA_FILES/sv_data_files/"
svdatabase = svbase+"profile_z%d_l%d.dat"
svcovbase  = svbase+"cov_t_z%d_l%d.dat"
svboostbase = svbase+"SV_boost_factors.txt"
svboostcovbase = "need_z%d_l%d"
svzspath   = svbase+"SV_meanz.txt"
svlamspath = svbase+"SV_meanl.txt"
#Sigma crit inverse path
SCIpath = "../photoz_calibration/sigma_crit_inv.txt"

h = 0.7
om = 0.3

def get_zs_and_lams(usey1):
    lams = get_lams(usey1)
    zs = get_zs(usey1)
    return zs, lams

def get_lams(usey1):
    if usey1: return np.genfromtxt(y1lamspath)
    else: return np.genfromtxt(svlamspath)

def get_zs(usey1):
    if usey1: return np.genfromtxt(y1zspath)
    else: return np.genfromtxt(svzspath)

def get_sigma_crit_inverses(usey1):
    if usey1: return np.loadtxt(SCIpath)
    else: return np.zeros((3,5))

def get_power_spectra(zi, lj, usey1):
    if usey1: base = y1base
    else: base = svbase
    k    = np.genfromtxt(base+"P_files/k.txt")
    Plin = np.genfromtxt(base+"P_files/plin_z%d_l%d.txt"%(zi, lj))
    Pnl  = np.genfromtxt(base+"P_files/pnl_z%d_l%d.txt"%(zi, lj))
    return k, Plin, Pnl
    
def get_data_and_icov(zi, lj, lowcut = 0.2, highcut = 999, usey1=True, alldata=False, useJK=True):
    #lowcut is the lower cutoff, assumed to be 0.2 Mpc physical
    #highcut might not be implemented in this analysis
    if usey1:
        print "Y1 data z%d l%d"%(zi, lj)
        datapath = y1database%(lj, zi)
        if useJK: covpath = y1JKcovbase%(lj, zi)
        else: covpath = y1SACcovbase%(zi, lj)
    else:
        print "SV data z%d l%d"%(zi, lj)
        datapath = svdatabase%(zi, lj)
        covpath = svcovbase%(zi, lj)
    R, ds, dse, dsx, dsxe = np.genfromtxt(datapath, unpack=True)
    cov = np.genfromtxt(covpath)
    if zi == 0 and not usey1: highcut=21.5 #Just for z0 in SV
    indices = (R > lowcut)*(R < highcut)
    if alldata: indices = R > 0.0
    R   = R[indices]
    ds  = ds[indices]
    cov = cov[indices]
    cov = cov[:,indices]
    #APPLY THE HARTLAP CORRECTION HERE
    if useJK:
        print "Hartlap applied"
        Njk = 100.
        D = len(R)
        cov = cov*((Njk-1.)/(Njk-D-2))
    return R, ds, np.linalg.inv(cov), cov, indices

def get_boost_data_and_cov(zi, lj, lowcut = 0.2, highcut = 999, usey1=True, alldata=False, diag_only=False):
    if usey1:
        boostpath = y1boostbase%(lj, zi)
        bcovpath  = y1boostcovbase%(lj, zi)
        #boostpath = y1boostbase%(zi, lj) #TEMP
        #bcovpath  = y1boostcovbase%(zi, lj) #TEMP
        Bcov = np.loadtxt(bcovpath)
        Rb, Bp1, Be = np.genfromtxt(boostpath, unpack=True)
        print Rb.shape, Bp1.shape, Be.shape, Bcov.shape
        Becut = Be > 1e-6
        Bp1 = Bp1[Becut]
        Rb  = Rb[Becut]
        Be  = Be[Becut]
        Bcov = Bcov[Becut]
        Bcov = Bcov[:,Becut]
        if alldata: #Still make this cut though
            return Rb, Bp1, np.linalg.inv(Bcov), Bcov
        indices = (Rb > lowcut)*(Rb < highcut)
        Bp1 = Bp1[indices]
        Rb  = Rb[indices]
        Be  = Be[indices]
        Bcov = Bcov[indices]
        Bcov = Bcov[:,indices]
        if diag_only: Bcov = np.diag(Be**2)
        #Note: the boost factors don't have the same number of radial bins
        #as deltasigma. This doesn't matter, because all we do is
        #de-boost the model, which fits to the boost factors independently.
        return Rb, Bp1, np.linalg.inv(Bcov), Bcov
    else: #use_sv
        print "SV boosts"
        boostpath = svboostbase
        bcovpath  = svboostcovbase%(zi, lj) #doesn't exist
        if zi == 0: highcut = 21.5 #1 degree cut
        Bp1, Rb = np.genfromtxt(boostpath, unpack=True, skip_header=1)
        #SV didn't have boost errors. We construct them instead
        del2 = 10**-4.09 #BF result from SV
        Be = np.sqrt(del2/Rb**2)
        if alldata:
            Bcov = np.diag(Be**2)
            return Rb, Bp1, np.linalg.inv(Bcov), Bcov
        indices = (Rb > lowcut)*(Rb < highcut)
        Bp1 = Bp1[indices]
        Rb  = Rb[indices]
        Be  = Be[indices]
        Bcov = np.diag(Be**2)
        return Rb, Bp1, np.linalg.inv(Bcov), Bcov

def get_cuts(zi, lj, usey1=True):
    lo = 0.2 #Mpc physical
    hi = 999.
    if not usey1 and zi==0: hi = 21.5
    return [lo, hi]

def get_model_defaults(h):
    #Dictionary of default starting points for the best fit
    defaults = {'lM'   : 14.37+np.log10(h), #Result of SV relation
                'conc'    : 4.5, #Arbitrary
                'tau' : 0.153, #Y1
                'fmis' : 0.32, #Y1
                'Am'    : 1.02, #Y1 approx.
                'B0'   : 0.07, #Y1
                'Rs'   : 2.49,  #Y1; Mpc physical
                'sig_b': 0.005} #Y1 boost scatter
    return defaults

def get_model_start(model_name, lam, h):
    defaults = get_model_defaults(h)
    #M is in Msun/h
    lM_guess = defaults['lM']+np.log(lam/30.)*1.12/np.log(10)
    if model_name is "full":
        guess = [lM_guess,
                 defaults['conc'],
                 defaults['tau'],
                 defaults['fmis'], 
                 defaults['Am'],
                 defaults['B0'],
                 defaults['Rs']]
    elif model_name is "Mc":
        guess = [lM_guess, 4.5]
    elif model_name is "M":
        guess = lM_guess
    return guess

def get_mcmc_start(model, model_name):
    lM, c, tau, fmis, Am, B0, Rs = model
    if model_name is "full":
        return model
    elif model_name is "Mc":
        return [lM, c]
    elif model_name is "M":
        return [lM,]
    
def get_cosmo_default():
    #The cosmology used in this analysis
    cosmo = {'h'      : 0.7,
             'om'     : 0.3,
             'ode'    : 0.7,
             'ob'     : 0.05,
             'ok'     : 0.0,
             'sigma8' : 0.8,
             'ns'     : 0.96}
    return cosmo

def get_Am_prior(zi, lj):
    #Photoz calibration (1+delta)
    deltap1 = np.loadtxt("../photoz_calibration/Y1_deltap1.txt")[zi, lj]
    deltap1_var = np.loadtxt("../photoz_calibration/Y1_deltap1_var.txt")[zi, lj]
    #Shear calibration m
    m = 0.012
    m_var = 0.013
    Am_prior = deltap1 + m
    Am_prior_var = deltap1_var + m_var
    return Am_prior, Am_prior_var

def get_Redges(usey1):
    #The bin edges in Mpc physical
    Nbins = 15
    if usey1: return np.logspace(np.log10(0.0323), np.log10(30.), num=Nbins+1)
    else: return np.logspace(np.log10(0.02), np.log10(30.), num=Nbins+1) #use_sv

#Set up the Concentration spline
def get_concentration_spline():
    from colossus.halo import concentration
    from colossus.cosmology import cosmology
    cos = {'flat':True,'H0':h*100.,'Om0':om,'Ob0':0.05,'sigma8':0.8,'ns':0.96}
    cosmology.addCosmology('fiducial', cos)
    cosmology.setCosmology('fiducial')
    N = 20
    M = np.logspace(12, 17, N)
    z = np.linspace(0.2, 0.65, N)
    c_array = np.ones((N, N))
    for i in range(N):
        for j in range(N):
            c_array[j,i] = concentration.concentration(M[i],'200m',z=z[j],model='diemer15')
    return interp2d(M, z, c_array)
