// webpack.config.js
const path = require('path');

module.exports = {
  entry: './js/main.js',
  output: {
    path: path.resolve(__dirname, 'dist/'),
    filename: 'bundle.js',
  },
  mode: 'production',
  "resolve": {
    "fallback": {
      "fs": false
    }
  }
};
