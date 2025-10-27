const path = require("path");
const WorkboxPlugin = require('workbox-webpack-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin')
let { merge } = require("webpack-merge");
const TerserPlugin = require("terser-webpack-plugin");

module.exports = merge(require("./webpack.common.cjs"), {
   mode: "production",
   output: {
      path: path.resolve(__dirname, "build"),
      filename: '[name].[contenthash].bundle.js',
      chunkFilename: '[name].[contenthash].chunk.js',
      clean: true,
   },
   module: {
      rules: [
         {
            test: /\.s[ac]ss$/i,
            use: [
               {
                  loader: MiniCssExtractPlugin.loader,
               },
               {
                  loader: 'css-loader',
                  options: { url: false }
               },
               {
                  loader: 'sass-loader',
                  options: {
                     api: "modern",
                  },
               },
            ],
         },
         {
            test: /\.mjs$/,
            include: /node_modules/,
            type: 'javascript/auto',
            resolve: {
               fullySpecified: false,
            },
         },
      ],
   },
   devtool: "source-map",
   plugins: [
      new WorkboxPlugin.GenerateSW({
         // these options encourage the ServiceWorkers to get in there fast
         // and not allow any straggling "old" SWs to hang around
         clientsClaim: true,
         skipWaiting: true,
         maximumFileSizeToCacheInBytes: 5000000,
      }),
      new MiniCssExtractPlugin({
         filename: 'styles.[name].[fullhash].min.css',
         chunkFilename: 'styles.[name].[contenthash].chunk.css',
      }),
   ],
   optimization: {
      minimizer: [
         new TerserPlugin({
            extractComments: false,
            terserOptions: {
               compress: {
                  drop_console: false, // Keep console for audit logs
                  passes: 2,
                  pure_funcs: ['console.debug'], // Remove debug logs only
               },
               mangle: true,
            },
         }),
         new CssMinimizerPlugin({
            minimizerOptions: {
               preset: [
                  'default',
                  {
                     discardComments: { removeAll: true },
                     normalizeWhitespace: true,
                     colormin: true,
                     minifyFontValues: true,
                     minifySelectors: true,
                  },
               ],
            },
         })
      ],
      minimize: true,
      splitChunks: {
         chunks: 'all',
         cacheGroups: {
            // Vendor code (node_modules)
            vendor: {
               test: /[\\/]node_modules[\\/]/,
               name: 'vendors',
               priority: 10,
               reuseExistingChunk: true,
            },
            // Ionic/Capacitor frameworks
            ionic: {
               test: /[\\/]node_modules[\\/](@ionic|@capacitor)[\\/]/,
               name: 'ionic',
               priority: 20,
               reuseExistingChunk: true,
            },
            // Crypto libraries (blake2, bs58, etc)
            crypto: {
               test: /[\\/]node_modules[\\/](blakejs|bs58|@noble|@scure)[\\/]/,
               name: 'crypto',
               priority: 15,
               reuseExistingChunk: true,
            },
            // Common code shared across routes
            common: {
               minChunks: 2,
               priority: 5,
               reuseExistingChunk: true,
               enforce: true,
            },
         },
      },
      runtimeChunk: 'single',
      moduleIds: 'deterministic',
   },
});
