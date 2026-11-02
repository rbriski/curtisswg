module.exports = {
  // Tailwind 2 purges only when NODE_ENV=production. Hugo does not pass NODE_ENV to
  // PostCSS (security.exec.osEnv filters it out) but always sets HUGO_ENVIRONMENT, so
  // key purging off that; otherwise production builds ship the full ~3 MB stylesheet.
  purge: {
    enabled: process.env.HUGO_ENVIRONMENT === 'production',
    content: ['layouts/**/*.html'],
  },
  darkMode: false, // or 'media' or 'class'
  theme: {
    extend: {},
  },
  variants: {
    extend: {},
  },
  plugins: [
    require('@tailwindcss/forms')
  ],
}
