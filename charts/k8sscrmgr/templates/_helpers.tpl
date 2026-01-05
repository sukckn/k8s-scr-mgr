{{/*
Return the base chart name
*/}}
{{- define "k8sscrmgr.chartName" -}}
    {{- .Chart.Name -}}
{{- end -}}


{{/*
Get release name without dash
*/}}
{{- define "k8sscrmgr.releaseNameClean" -}}
    {{- replace "-" "" .Release.Name -}}
{{- end -}}


{{/*
Return a fully qualified name: <release>-<name>
Respects installName to force a specific root name.
*/}}
{{- define "k8sscrmgr.installName" -}}
    {{- if eq (include "k8sscrmgr.chartName" .) (include "k8sscrmgr.releaseNameClean" .) -}}
        {{- printf "%s" .Release.Name | trunc 63 | trimSuffix "-" -}}
    {{- else -}}
        {{- printf "%s-%s" .Release.Name (include "k8sscrmgr.chartName" .) | trunc 63 | trimSuffix "-" -}}
    {{- end -}}
{{- end -}}

{{/*
Common labels to apply to all resources.
*/}}
{{- define "k8sscrmgr.labels" -}}
app.kubernetes.io/name: {{ include "k8sscrmgr.chartName" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/version: {{ .Chart.AppVersion | default .Chart.Version }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | quote }}
{{- end -}}

{{/*
Uninstall command.
*/}}
{{- define "k8sscrmgr.uninstall" -}}
    {{- printf "helm uninstall %s -n %s" .Release.Name .Release.Namespace -}}
{{- end -}}

