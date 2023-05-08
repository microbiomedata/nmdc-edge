const JwtStrategy = require("passport-jwt").Strategy;
const ExtractJwt = require("passport-jwt").ExtractJwt;
const mongoose = require("mongoose");

const User = mongoose.model("users");
const logger = require("./logger");

const opts = {};
opts.jwtFromRequest = ExtractJwt.fromAuthHeaderAsBearerToken();
opts.secretOrKey = process.env.JWT_KEY;

module.exports = passport => {
    passport.use(
        'user',
        new JwtStrategy(opts, (jwt_payload, done) => {
            User.findById(jwt_payload.id)
                .then(user => {
                    if (user && user.status === "active") {
                        return done(null, user);
                    }
                    return done(null, false);
                })
                .catch(err => {
                    logger.error(err);
                });
        })
    );

    passport.use(
        'admin',
        new JwtStrategy(opts, (jwt_payload, done) => {
            User.findById(jwt_payload.id)
                .then(user => {
                    if (user && user.status === "active" && user.type === 'admin') {
                        return done(null, user);
                    }
                    return done(null, false);
                })
                .catch(err => {
                    logger.error(err);
                });
        })
    );
}