FROM anywayteam/anyway:latest AS builder
RUN flask assets build

FROM nginx:stable
COPY --from=builder /anyway/static /opt/anyway/static
COPY default.conf /etc/nginx/conf.d/default.conf
COPY anyway_upstream.conf /etc/nginx/anyway_upstream.conf
COPY anyway_proxy.conf /etc/nginx/anyway_proxy.conf
