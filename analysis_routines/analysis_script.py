import numpy as np
from likelihood_functions import *
from helper_functions import *
import models
import sys
import clusterwl #Used to get xi_mm(R) from P(k)
import blinding
Blinding_amp, lam_exp, z_exp = blinding.get_blinding_variables()

#Set up the assumptions
cosmo = get_cosmo_default()
h = cosmo['h'] #Hubble constant

model_name = "Mc" #Mfree, Afixed, cfixed

def find_best_fit(bf_args, bestfitpath, bestfitvarpath, usey1):
    z, lam, Rlam, ds, icov, cov, Rb, Bp1, iBcov, Bcov, k, Plin, Pnl, Rmodel, xi_mm, Redges, inds, Am_prior, Am_prior_var, sigma_crit_inv, model_name = bf_args
    guess = get_model_start(model_name, lam, h)
    import scipy.optimize as op
    nll = lambda *args: -lnprob(*args)
    result = op.minimize(nll, guess, args=(bf_args,), tol=1e-2)
    print "Best fit being saved at :\n%s"%bestfitpath
    #print result
    #print "\tresults: ",result['x']
    print "\tsuccess = %s"%result['success']
    ihess = result['hess_inv']
    #print "lM = %.3f"%(lM - np.log10(h))
    outmodel = models.model_swap(result['x'], model_name)
    if usey1: outmodel[0]+= np.log10(Blinding_amp) +  np.log10((lam/30.0)**lam_exp) + np.log10(((1+z)/1.5)**z_exp)
    np.savetxt(bestfitpath, outmodel)
    np.savetxt(bestfitvarpath, ihess)
    return 

def do_mcmc(args, bfpath, chainpath, likespath, usey1):
    nwalkers, nsteps = 32, 5000
    import emcee
    z, lam, Rlam, ds, icov, cov, Rb, Bp1, iBcov, Bcov, k, Plin, Pnl, Rmodel, xi_mm, Redges, inds, Am_prior, Am_prior_var, sigma_crit_inv, model_name = args
    bfmodel = np.loadtxt(bfpath) #Has everything
    start = get_mcmc_start(bfmodel, model_name)
    ndim = len(start) #number of free parameters
    pos = [start + 1e-3*np.random.randn(ndim) for k in range(nwalkers)]
    print model_name
    sampler = emcee.EnsembleSampler(nwalkers, ndim, lnprob, args=(args,), threads=4)
    print "Starting MCMC, saving to %s"%chainpath
    sampler.run_mcmc(pos, nsteps)
    print "MCMC complete"
    #np.savetxt(chainpath, sampler.flatchain)
    #np.savetxt(likespath, sampler.flatlnprobability)
    return 0

if __name__ == '__main__':
    usey1 = False
    blinded = False
    zs, lams = get_zs_and_lams(usey1 = usey1)
    Rlams = (lams/100.0)**0.2 #Mpc/h; richness radius
    SCIs = get_sigma_crit_inverses(usey1)

    #This specifies which analysis we are doing
    #Name options are full, fixed, boostfixed or Afixed
    if usey1:
        name = "y1"
        if blinded: bstatus = "blinded"
        else: bstatus = "unblinded"
    else:
        name = "sv"
        bstatus = "unblinded"
    basesuffix = bstatus+"_"+name+"_z%d_l%d"    
    bestfitbase = "bestfits/bf_%s.txt"%basesuffix
    bestfitvarbase = "bestfits/bf_ihess_%s.txt"%basesuffix
    chainbase   = "chains/chain_%s.txt"%basesuffix
    likesbase   = "chains/likes_%s.txt"%basesuffix

    import matplotlib.pyplot as plt
    #Loop over bins
    for i in xrange(0, -1, -1): #z bins
        if i > 0 : continue
        for j in xrange(3, 2, -1): #lambda bins
            if j > 3 or j < 3: continue
            print "Working at z%d l%d for %s"%(i,j,name)
            z    = zs[i,j]
            lam  = lams[i,j]
            Rlam = Rlams[i,j]
            sigma_crit_inv = SCIs[i,j]/(h*(1+z)**2) #Convert to Msun h/pc^2 comoving
            k, Plin, Pnl = get_power_spectra(i, j, usey1)
            Rmodel = np.logspace(-2, 3, num=1000, base=10) 
            xi_mm = clusterwl.xi.xi_mm_at_R(Rmodel, k, Pnl)
            #Xi_mm MUST be evaluated to higher than BAO for correct accuracy

            #Note: convert Rlam to Mpc physical when we specificy the cuts
            Rdata, ds, icov, cov, inds = get_data_and_icov(i, j, usey1=usey1)

            Rb, Bp1, iBcov, Bcov = get_boost_data_and_cov(i, j, usey1=usey1)
            bfpath    = bestfitbase%(i, j)
            bfvarpath = bestfitvarbase%(i, j)
            chainpath = chainbase%(i, j)
            likespath = likesbase%(i, j)

            #Multiplicative prior
            Am_prior, Am_prior_var = get_Am_prior(i, j)

            #Group everything up for convenience
            Redges = get_Redges(usey1 = usey1)*h*(1+z) #Mpc/h comoving
            args = (z, lam, Rlam, ds, icov, cov, Rb, Bp1, iBcov, Bcov, k, Plin, Pnl, Rmodel, xi_mm, Redges, inds, Am_prior, Am_prior_var, sigma_crit_inv, model_name)

            #Flow control for whatever you want to do
            #find_best_fit(args, bfpath, bfvarpath, usey1)
            do_mcmc(args, bfpath, chainpath, likespath, usey1)
