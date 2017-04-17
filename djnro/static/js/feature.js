/**
 * AMD-Feature - A loader plugin for AMD loaders.
 *
 * https://github.com/jensarps/AMD-feature
 *
 * @author Jens Arps - http://jensarps.de/
 *   modified by Zenon Mousmoulas, GRNET
 *   fork: https://github.com/zmousm/AMD-feature
 * @license MIT or BSD - https://github.com/jensarps/AMD-feature/blob/master/LICENSE
 * @version 1.2.0
 */
;(function(factory) {
  if (typeof define === 'function' && define.amd) {
    // we define two modules, and each may use different 'implementations'
    // no way to do this in one file, without hardcoding the module name
    define('feature',  ['module'], factory);
    define('polyfill', ['module'], factory);
  }
}(function(module) {
  'use strict';

  var ourName = module.id;

  // Check availability of implementation
  function isAvailable (impl, name) {
    var isFunction = typeof impl.isAvailable === 'function';
    return (isFunction && impl.isAvailable(name)) || (!isFunction && impl.isAvailable);
  }

  function preemptDefinition(config) {
    var preemptOption = ourName + '_preempt';
    return !!config[preemptOption] && Boolean(config[preemptOption]);
  }

  return {

    load: function (name, req, load, config) {
      var implementations = config[ourName + '_implementations'] || 'implementations';

      req([implementations], function(implementations) {

	var i, impl, m, toLoad,
            featureInfo = implementations[name],
            hasMultipleImpls = Object.prototype.toString.call(featureInfo) === '[object Array]';

	if (config.isBuild && hasMultipleImpls) {
          // In build context, we want all possible
          // implementations included.
          for (i = 0, m = featureInfo.length; i < m; i++) {
            impl = featureInfo[i].implementation;
            if (typeof impl === 'function') {
              impl = impl.call(featureInfo[i], name);
            }
            if (impl) {
	      if (preemptDefinition(config)) {
		req([toLoad], function(alias) {
		  define(name, [], alias);
		  load(alias);
		});
	      } else {
		req([impl], load);
	      }
            }
          }

          // We're done here now.
          return;
	}

	if (hasMultipleImpls) {
          // We have different implementations available,
          // test for the one to use.
          for (i = 0, m = featureInfo.length; i < m; i++) {
            impl = featureInfo[i];
            if (isAvailable(impl, name)) {
              break;
            }
            impl = null;
          }
	} else {
          impl = featureInfo;
          // The only implementation can have isAvailable check
          if (impl && typeof impl === 'object' && ('isAvailable' in impl) &&
	      !isAvailable(impl, name)) {
            impl = null;
          }
	}

	if (impl) {
          if (typeof impl === 'string') {
            toLoad = impl;
          } else if (typeof impl === 'object' && ('module' in impl)) {
            toLoad = typeof impl.module === 'function' ? impl.module(name) : impl.module;
	    if (preemptDefinition(config)) {
	      define(name, [], toLoad);
	    }
	    load(toLoad);
            return;
          } else {
            toLoad = impl.implementation;
            if (typeof toLoad === 'function') {
              toLoad = impl.implementation(name);
            }
          }
	  if (preemptDefinition(config)) {
	    req([toLoad], function(alias) {
	      define(name, [], alias);
	      load(alias);
	    });
	  } else {
            req([toLoad], load);
	  }
	} else {
          req([name], load);
	}

      });

    }
  };
}));
