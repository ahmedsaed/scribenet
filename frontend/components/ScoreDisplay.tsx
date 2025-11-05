'use client';

export interface QualityScore {
  category: string;
  score: number;
  maxScore: number;
  description?: string;
}

interface ScoreDisplayProps {
  scores: QualityScore[];
  overallScore?: number;
}

const getScoreColor = (percentage: number) => {
  if (percentage >= 80) return 'from-green-500 to-emerald-500';
  if (percentage >= 60) return 'from-yellow-500 to-orange-500';
  return 'from-red-500 to-rose-500';
};

const getScoreTextColor = (percentage: number) => {
  if (percentage >= 80) return 'text-green-600';
  if (percentage >= 60) return 'text-yellow-600';
  return 'text-red-600';
};

const getScoreBgColor = (percentage: number) => {
  if (percentage >= 80) return 'bg-green-50';
  if (percentage >= 60) return 'bg-yellow-50';
  return 'bg-red-50';
};

export default function ScoreDisplay({ scores, overallScore }: ScoreDisplayProps) {
  return (
    <div>
      {overallScore !== undefined && (
        <div className={`mb-6 rounded-xl p-6 text-center ${getScoreBgColor(overallScore)}`}>
          <div className={`text-5xl font-bold mb-2 ${getScoreTextColor(overallScore)}`}>
            {overallScore}
            <span className="text-2xl text-gray-500">/100</span>
          </div>
          <div className="text-sm font-semibold text-gray-700 mb-3">Overall Score</div>
          <div className="w-full bg-white/50 rounded-full h-2 overflow-hidden">
            <div
              className={`h-full bg-gradient-to-r ${getScoreColor(overallScore)} transition-all duration-500`}
              style={{ width: `${overallScore}%` }}
            />
          </div>
        </div>
      )}

      <div className="space-y-3">
        {scores.map((score, index) => {
          const percentage = (score.score / score.maxScore) * 100;
          return (
            <div key={index} className="bg-gray-50 rounded-lg p-3">
              <div className="flex justify-between items-start mb-2">
                <div className="flex-1">
                  <span className="font-semibold text-sm text-gray-900">{score.category}</span>
                  {score.description && (
                    <p className="text-xs text-gray-600 mt-0.5">{score.description}</p>
                  )}
                </div>
                <span className={`text-base font-bold ${getScoreTextColor(percentage)} ml-2`}>
                  {score.score}
                  <span className="text-xs text-gray-500">/{score.maxScore}</span>
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
                <div
                  className={`h-full bg-gradient-to-r ${getScoreColor(percentage)} transition-all duration-500`}
                  style={{ width: `${percentage}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {scores.length === 0 && overallScore === undefined && (
        <div className="text-center py-12 text-gray-500">
          <svg className="w-16 h-16 mx-auto mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <p className="text-sm font-medium">No Metrics Yet</p>
          <p className="text-xs mt-1">Complete chapters to see quality scores</p>
        </div>
      )}
    </div>
  );
}
