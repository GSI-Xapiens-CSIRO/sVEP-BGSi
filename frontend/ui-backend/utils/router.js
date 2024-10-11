import _ from 'lodash';

export function build_response(code, body) {
  return {
    statusCode: code,
    body: JSON.stringify(body),
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Credentials': true,
    },
  };
}

function match_regex_path(template_path, proxy_path) {
  // Convert the template_path into a regex pattern
  // Replace {variable} with a regex group that matches anything except for '/'
  const pattern = template_path.replace(/{\w+}/g, '([^\/]+)');

  // Create a new RegExp object with the pattern
  const regex = new RegExp(`^${pattern}$`);

  // Match the proxy_path against the regex
  const match = proxy_path.match(regex);

  if (match) {
    // Extract the variable names from the template
    const path_param_variables = (template_path.match(/{\w+}/g) || []).map(v => v.slice(1, -1));

    // Create the params object
    let params = {};

    // Start from 1 as match[0] is the full string
    for (let i = 1; i < match.length; i++) {
      params[path_param_variables[i - 1]] = match[i];
    }

    return params;
  }

  return false;
}

export function ProxyRouter(event, context, callback) {
  console.log('EVENT RECEIVED', event)
  this.path = _.trim(_.get(event, 'pathParameters.proxy', ''), '/');
  this.method = event.httpMethod;
  this.callback = callback;

  this.route = function (method, path, handler) {
    const matched_params = match_regex_path(_.trim(path, '/'), this.path);
    if (this.method === method && matched_params) {
      try {
        if (method !== 'GET') {
          _.assign(event, { 'pathParameters': matched_params })
          event.body = JSON.parse(event.body);
        }
        handler(event, context, callback);
      } catch (e) {
        console.log(e);
        this.callback(null, builResponse(500, "Data Error"));
      }
    }
  }
}