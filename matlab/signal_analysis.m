% OPTIONAL MATLAB analysis of the signals exported by the Python project.
% Run first:  python -m experiments.run_experiments   (creates results/signal_export.csv)
% Needs Signal Processing Toolbox (butter, filtfilt). NOT executed by the project author's tooling:
% treat as a cross-check template and verify in your own MATLAB.
T = readtable('../results/signal_export.csv');
fs = round(1/(T.t_s(2)-T.t_s(1)));
snr = @(ref,x) 10*log10(sum(ref.^2)/sum((ref-x).^2));
x = T.original; y = T.noisy;
fprintf('SNR noisy (Python export)            : %.2f dB\n', snr(x,y));
fprintf('SNR Kalman (Python)                  : %.2f dB\n', snr(x,T.kalman));
fprintf('SNR LMS (Python)                     : %.2f dB\n', snr(x,T.lms));
fprintf('SNR Wiener (Python)                  : %.2f dB\n', snr(x,T.wiener));
fprintf('SNR Butterworth/final (Python)       : %.2f dB\n', snr(x,T.butterworth));
% Independent MATLAB cross-check of the last stage: 4th-order low-pass Butterworth, zero phase
fc = 0.25*fs;                                   % example cutoff, change as needed
[b,a] = butter(4, fc/(fs/2)); yb = filtfilt(b,a,y);
fprintf('SNR MATLAB Butterworth on noisy only : %.2f dB\n', snr(x,yb));
% Manual NLMS line enhancer (no toolbox)
taps = 32; mu = 0.05; D = 1; w = zeros(taps,1); n = numel(y); yl = zeros(n,1); p = [zeros(taps+D,1); y(:)];
for i = 1:n
    j = i+taps+D; u = flipud(p(j-D-taps+1:j-D)); yl(i) = w.'*u; e = y(i)-yl(i); w = w + mu*e*u/(1e-8+u.'*u);
end
fprintf('SNR MATLAB NLMS on noisy only        : %.2f dB\n', snr(x,yl));
t = T.t_s*1000;
figure; subplot(3,1,1); plot(t,x); title('Original'); subplot(3,1,2); plot(t,y); title('Noisy');
subplot(3,1,3); plot(t,T.butterworth); title('Python final output'); xlabel('Time (ms)');
figure; spectrogram(y, 512, 384, 512, fs, 'yaxis'); title('Noisy spectrogram');
